"""
SeamFormer-based text line segmentation service.

Refactored from line_segmenting.py (Kaggle notebook) into a reusable class.
Uses the SeamFormer model for:
  - Stage 1: Binary map + Scribble map generation
  - Post-processing: Scribble refinement
  - Stage 2: Seam-conditioned polygon generation

Lontar-specific fixes applied on top of vanilla SeamFormer:
  - Row separation pre-processing: vertical morphological opening on the binary
    map widens tight inter-row gaps so adjacent lontar rows are not fused into
    a single scribble hull.
  - Configurable hull merge tolerance: reduced from SeamFormer's default 30 px
    so closely spaced rows are kept as separate scribble lines.
  - Merged-line splitter: any polygon whose height exceeds
    `line_merge_split_ratio x median_height` is analysed with a horizontal
    projection profile; if a clear ink valley is found it is split into two.
  - Diacritic vertical padding: each line crop is expanded vertically by
    `diacritic_padding_ratio x line_height` so pengangge / gantungan marks
    that sit above or below the core glyph body are always included.
"""

import gc
import logging
import sys

import cv2
import numpy as np
import torch
from empatches import EMPatches
from scipy.ndimage import uniform_filter1d
from vit_pytorch.vit import ViT

from app.config import SEAMFORMER_DIR, SEAMFORMER_SETTINGS

# Add seamformer directory to path so we can import its modules
sys.path.insert(0, str(SEAMFORMER_DIR))
from network import SeamFormer
from seam_conditioned_scribble_generation import imageTask
from utils import (
    cleanImageFindContours,
    combine_hulls_on_same_level,
    generateScribble,
    horizontal_dilation,
    polygon_to_distance_mask,
    readFullImage,
    reconstruct,
    text_dilate,
)

logger = logging.getLogger(__name__)


class SegmentationResult:
    """Container for segmentation results."""

    def __init__(
        self,
        binary_map: np.ndarray,
        scribble_map: np.ndarray,
        segmentation_vis: np.ndarray,
        line_images: list[np.ndarray],
        polygons: list,
    ):
        self.binary_map = binary_map
        self.scribble_map = scribble_map
        self.segmentation_vis = segmentation_vis
        self.line_images = line_images
        self.polygons = polygons


class SeamFormerService:
    """SeamFormer text line segmentation service."""

    _instance = None

    def __init__(self, weights_path: str, device: str = "cpu"):
        self.device = torch.device(device)
        self.settings = SEAMFORMER_SETTINGS
        self.network = self._build_model(weights_path)
        logger.info("SeamFormer model loaded on device: %s", self.device)

    @classmethod
    def get_instance(cls, weights_path: str, device: str = "cpu"):
        """Singleton pattern to avoid loading the model multiple times."""
        if cls._instance is None:
            cls._instance = cls(weights_path, device)
        return cls._instance

    def _build_model(self, weights_path: str) -> SeamFormer:
        """Build and load the SeamFormer network."""
        v = ViT(
            image_size=self.settings["img_size"],
            patch_size=self.settings["patch_size"],
            num_classes=1000,
            dim=self.settings["encoder_dims"],
            depth=self.settings["encoder_layers"],
            heads=self.settings["encoder_heads"],
            mlp_dim=2048,
        )
        network = SeamFormer(
            encoder=v,
            decoder_dim=self.settings["encoder_dims"],
            decoder_depth=self.settings["encoder_layers"],
            decoder_heads=self.settings["encoder_heads"],
            patch_size=self.settings["patch_size"],
        )
        logger.info("Loading SeamFormer weights from: %s", weights_path)
        network.load_state_dict(
            torch.load(weights_path, map_location=self.device),
            strict=True,
        )
        network = network.to(self.device)
        network.eval()
        return network

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def process(self, image_path: str) -> SegmentationResult:
        """
        Run full segmentation pipeline on an image.

        Args:
            image_path: Path to the input image file.

        Returns:
            SegmentationResult with binary map, scribble map,
            visualization, and extracted line images.
        """
        # Read original image
        img_original = cv2.imread(image_path)
        if img_original is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")

        H, W, _ = img_original.shape
        logger.info("Processing image: %s (%dx%d)", image_path, W, H)

        # ── Stage 1: Inference → Binary + Scribble maps ──────────────────
        binary_map, scribble_map = self._image_inference(image_path)
        binary_map = np.uint8(binary_map)
        scribble_map = np.uint8(scribble_map)
        logger.info(
            "Stage 1 complete: binary=%s, scribble=%s",
            binary_map.shape,
            scribble_map.shape,
        )

        # ── Row separation pre-processing ────────────────────────────────
        # Apply a vertical morphological opening to the binary map so that
        # tight inter-row gaps (common in lontar manuscripts) are widened
        # before scribble detection.  We keep the *original* binary_map for
        # Stage 2 so the seam generator still sees the full ink image.
        binary_for_scribble = self._separate_rows(binary_map)

        # ── Post-processing: Refine scribbles ────────────────────────────
        scribbles = self._post_process(scribble_map, binary_for_scribble)
        logger.info("Post-processing: %d scribbles found", len(scribbles))

        if len(scribbles) == 0:
            logger.warning("No scribbles detected — returning empty result")
            return SegmentationResult(
                binary_map=binary_map,
                scribble_map=scribble_map,
                segmentation_vis=img_original.copy(),
                line_images=[],
                polygons=[],
            )

        # ── Stage 2: Seam generation → polygons ──────────────────────────
        # Convert *original* binary map to 3-channel for imageTask
        bin_3ch = cv2.cvtColor(binary_map, cv2.COLOR_GRAY2BGR)
        polygons = imageTask(img_original, bin_3ch, scribbles)
        logger.info("Stage 2 complete: %d text line polygons", len(polygons))

        # ── Split any merged-row polygons ─────────────────────────────────
        polygons = self._split_merged_lines(polygons, binary_map)
        logger.info("After split pass: %d polygons", len(polygons))

        # Sort top-to-bottom for consistent ordering
        polygons = self._sort_polygons_top_to_bottom(polygons)

        # ── Visualise polygons on original image ──────────────────────────
        seg_vis = self._draw_polygons(img_original, polygons)

        # ── Extract line images with diacritic padding ────────────────────
        line_images = self._extract_lines(img_original, polygons)

        gc.collect()

        return SegmentationResult(
            binary_map=binary_map,
            scribble_map=scribble_map,
            segmentation_vis=seg_vis,
            line_images=line_images,
            polygons=polygons,
        )

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    # ── Stage 1 ──────────────────────────────────────────────────────── #

    def _image_inference(
        self, path: str, pdim: int = 256, dim: int = 256, overlap: float = 0.25
    ) -> tuple[np.ndarray, np.ndarray]:
        """Run Stage 1 inference: generate binary and scribble maps."""
        emp = EMPatches()
        weight = torch.tensor(1)

        input_patches, indices = readFullImage(path, pdim, dim, overlap)
        if input_patches is None:
            raise ValueError(f"Failed to read image patches from: {path}")

        patch_size = self.settings["patch_size"]
        img_size = self.settings["img_size"]
        split_size = self.settings["split_size"]
        image_size = (split_size, split_size)
        threshold = self.settings["threshold"]

        soutput_patches = []
        boutput_patches = []

        for i, sample in enumerate(input_patches):
            p = sample["img"]
            target_shape = (sample["resized"][1], sample["resized"][0])

            with torch.no_grad():
                inputs = torch.from_numpy(p).to(self.device)
                loss_criterion = torch.nn.BCEWithLogitsLoss(
                    pos_weight=weight, reduction="none"
                )
                pred_bin, pred_scr = self.network(
                    inputs,
                    gt_bin_img=inputs,
                    gt_scr_img=inputs,
                    criterion=loss_criterion,
                    strain=True,
                    btrain=True,
                    mode="test",
                )
                pred_bin = pred_bin.cpu()
                pred_scr = pred_scr.cpu()

                bpatch = reconstruct(pred_bin, patch_size, target_shape, image_size)
                spatch = reconstruct(pred_scr, patch_size, target_shape, image_size)

                bpatch = (bpatch > threshold) * 1
                spatch = (spatch > threshold) * 1

                soutput_patches.append(255 * spatch)
                boutput_patches.append(255 * bpatch)

        soutput = emp.merge_patches(soutput_patches, indices, mode="max")
        boutput = emp.merge_patches(boutput_patches, indices, mode="max")

        binary_output = np.transpose(boutput, (1, 0))
        scribble_output = np.transpose(soutput, (1, 0))

        return binary_output, scribble_output

    # ── Row separation ────────────────────────────────────────────────── #

    def _separate_rows(self, binary_map: np.ndarray) -> np.ndarray:
        """
        Widen the inter-row gaps in the binary map with a vertical
        morphological opening.

        Lontar manuscripts have tightly packed rows ("mepet").  Diacritics
        that extend above/below the core glyph can physically bridge the gap
        between two rows, causing the scribble detector to fuse them.

        A morphological opening with a vertical kernel (height = kernel_size,
        width = 1) erodes thin vertical bridges between rows while preserving
        the bulk of each glyph body.  The subsequent dilation step restores
        the main ink region.

        The original binary_map is NOT modified; a new array is returned so
        Stage 2 can still use the full un-eroded binary.
        """
        kernel_size = self.settings.get("row_separation_kernel", 3)
        if kernel_size < 2:
            return binary_map.copy()

        vkernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, int(kernel_size)))
        separated = cv2.morphologyEx(binary_map, cv2.MORPH_OPEN, vkernel)
        logger.debug(
            "Row separation applied (kernel=%dpx); white px before=%d after=%d",
            kernel_size,
            int(np.sum(binary_map > 0)),
            int(np.sum(separated > 0)),
        )
        return separated

    # ── Post-processing ───────────────────────────────────────────────── #

    def _post_process(
        self,
        scribble_image: np.ndarray,
        binary_image: np.ndarray,
        binary_threshold: int = 40,
        rectangular_kernel: int = 30,
    ) -> list:
        """
        Refine scribble maps into clean scribble lines.

        Lontar fix: uses `hull_merge_tolerance` from settings (default 15 px)
        instead of SeamFormer's hard-coded 30 px so closely-spaced rows are
        not fused into one scribble hull.
        """
        scr = np.repeat(scribble_image[:, :, np.newaxis], 3, axis=2)
        bin_img = np.repeat(binary_image[:, :, np.newaxis], 3, axis=2)
        bin_img = bin_img.astype(np.uint8)
        scr = scr.astype(np.uint8)

        H, W, _ = bin_img.shape

        tmp = polygon_to_distance_mask(scr, threshold=30)
        final_tmp = np.zeros_like(scr)
        for j in range(3):
            final_tmp[:, :, j] = tmp
        scr = final_tmp

        bin_img[bin_img >= binary_threshold] = 255
        bin_img[bin_img < binary_threshold] = 0
        scr[scr >= binary_threshold] = 255
        scr[scr < binary_threshold] = 0

        scr_ = cv2.bitwise_and(bin_img / 255, scr / 255)
        scr_ = text_dilate(scr_, kernel_size=3, iterations=3)
        scr_ = horizontal_dilation(scr_, rectangular_kernel, 1)

        contours = cleanImageFindContours(scr_, threshold=0.10)
        if contours is None or len(contours) == 0:
            return []

        # Use a tighter merge tolerance so mepet lontar rows stay separate
        hull_tolerance = self.settings.get("hull_merge_tolerance", 15)
        new_hulls = combine_hulls_on_same_level(contours, tolerance=hull_tolerance)

        predicted_scribbles = []
        for c in new_hulls:
            canvas_copy = np.zeros(scr_.shape)
            c = np.asarray(c, dtype=np.int32).reshape((-1, 1, 2))
            canvas_copy = cv2.fillPoly(canvas_copy, np.int32([c]), (255, 255, 255))

            contours_inner = cleanImageFindContours(canvas_copy, threshold=0.10)
            if contours_inner is None or len(contours_inner) == 0:
                continue

            h = np.asarray(contours_inner[0], dtype=np.int32)
            h = cv2.convexHull(h)
            h = np.asarray(h, dtype=np.int32).reshape((-1, 2))
            h = h.tolist()
            scr_line = generateScribble(H, W, h)
            scr_arr = np.asarray(scr_line, dtype=np.int32).reshape((-1, 1, 2))
            scr_lst = scr_arr.reshape((-1, 2)).tolist()
            predicted_scribbles.append(scr_lst)

        return predicted_scribbles

    # ── Merged-row splitter ───────────────────────────────────────────── #

    def _split_merged_lines(
        self,
        polygons: list,
        binary_map: np.ndarray,
    ) -> list:
        """
        Detect polygons that contain two merged text rows and split them.

        Algorithm
        ---------
        1. Compute the median polygon height over all detected polygons.
        2. Any polygon whose height exceeds `line_merge_split_ratio x
           median_height` is a candidate for splitting.
        3. For each candidate, crop the binary map to the polygon's bounding
           box and compute the horizontal projection profile (ink pixels per
           row).
        4. Smooth the profile with a uniform filter and search for the
           deepest ink valley in the middle 50 % of the polygon height.
        5. If the valley is sufficiently deep relative to the ink peaks on
           both sides (`valley < 0.25 x min(upper_peak, lower_peak)`), split
           the polygon there and replace it with two rectangular polygons.

        The split threshold and ratio are configurable via SEAMFORMER_SETTINGS.
        """
        if len(polygons) < 2:
            return polygons

        split_ratio = self.settings.get("line_merge_split_ratio", 1.8)
        H_img, W_img = binary_map.shape[:2]

        # Compute heights for all polygons
        heights = []
        bboxes = []
        for poly in polygons:
            pts = np.asarray(poly, dtype=np.int32).reshape((-1, 2))
            x, y, w, h = cv2.boundingRect(pts)
            heights.append(h)
            bboxes.append((x, y, w, h))

        median_h = float(np.median(heights))
        if median_h <= 0:
            return polygons

        result_polygons: list = []
        split_count = 0

        for poly, (x, y, w, h) in zip(polygons, bboxes):
            if h < split_ratio * median_h:
                result_polygons.append(poly)
                continue

            # ── Candidate for splitting ───────────────────────────────── #
            # Clamp bounding box to image
            cx = max(0, x)
            cy = max(0, y)
            cw = min(w, W_img - cx)
            ch = min(h, H_img - cy)

            if cw <= 0 or ch < 6:
                result_polygons.append(poly)
                continue

            # Horizontal projection profile (ink pixels per row)
            crop = binary_map[cy : cy + ch, cx : cx + cw]
            proj = np.sum(crop > 128, axis=1).astype(float)

            # Smooth to reduce noise
            smooth_size = max(3, ch // 10)
            proj_smooth = uniform_filter1d(proj, size=smooth_size)

            # Search for valley in the middle 50 % (avoid polygon edges)
            margin = ch // 4
            search = proj_smooth[margin : ch - margin]
            if len(search) < 3:
                result_polygons.append(poly)
                continue

            valley_rel = int(np.argmin(search))
            valley_abs = valley_rel + margin  # row index inside the crop

            valley_val = proj_smooth[valley_abs]
            upper_peak = (
                float(np.max(proj_smooth[:valley_abs])) if valley_abs > 0 else 0.0
            )
            lower_peak = (
                float(np.max(proj_smooth[valley_abs + 1 :]))
                if valley_abs < ch - 1
                else 0.0
            )

            # Only split when the valley is clearly an inter-row gap
            min_peak = min(upper_peak, lower_peak)
            deep_enough = (min_peak > 0) and (valley_val < 0.25 * min_peak)

            if deep_enough:
                split_y_abs = cy + valley_abs  # absolute Y in the full image

                # Create two rectangular polygons for the two sub-lines
                poly_top = [
                    [cx, cy],
                    [cx + cw, cy],
                    [cx + cw, split_y_abs],
                    [cx, split_y_abs],
                ]
                poly_bot = [
                    [cx, split_y_abs],
                    [cx + cw, split_y_abs],
                    [cx + cw, cy + ch],
                    [cx, cy + ch],
                ]
                result_polygons.extend([poly_top, poly_bot])
                split_count += 1
                logger.info(
                    "Split merged polygon h=%d at row %d "
                    "(valley=%.1f upper_peak=%.1f lower_peak=%.1f)",
                    ch,
                    valley_abs,
                    valley_val,
                    upper_peak,
                    lower_peak,
                )
            else:
                result_polygons.append(poly)

        if split_count:
            logger.info(
                "Merged-row splitter: split %d polygon(s); total now %d",
                split_count,
                len(result_polygons),
            )
        return result_polygons

    # ── Polygon utilities ─────────────────────────────────────────────── #

    @staticmethod
    def _sort_polygons_top_to_bottom(polygons: list) -> list:
        """Sort polygons by their vertical centroid (top to bottom)."""

        def _centroid_y(poly):
            pts = np.asarray(poly, dtype=np.float32).reshape((-1, 2))
            return float(np.mean(pts[:, 1]))

        return sorted(polygons, key=_centroid_y)

    def _draw_polygons(self, image: np.ndarray, polygons: list) -> np.ndarray:
        """Draw text line polygons on the original image."""
        result = image.copy()
        colors = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
        ]
        for idx, p in enumerate(polygons):
            p_arr = np.asarray(p, dtype=np.int32).reshape((-1, 1, 2))
            color = colors[idx % len(colors)]
            result = cv2.polylines(result, [p_arr], True, color, 2)

            centroid = np.mean(p_arr.reshape(-1, 2), axis=0).astype(int)
            cv2.putText(
                result,
                f"Line {idx + 1}",
                tuple(centroid),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
                cv2.LINE_AA,
            )
        return result

    # ── Line extraction with diacritic padding ────────────────────────── #

    def _extract_lines(self, image: np.ndarray, polygons: list) -> list[np.ndarray]:
        """
        Extract line images that follow the polygon curvature with diacritic padding.

        Strategy
        --------
        1. Render the seam-conditioned polygon as a binary mask — this mask
           already follows the natural top/bottom curves of the text line.
        2. Dilate the mask **vertically** by `diacritic_padding_ratio × height`
           pixels.  This expands the masked region above and below the polygon
           boundary so that pengangge suara, gantungan, and pengangge tengenan
           marks (which sit outside the tight polygon) are always included.
        3. Apply the dilated mask to the image (pixels outside → white background)
           and crop to the mask's bounding box.

        Result: the top and bottom edges of each crop follow the polygon's
        natural curves (not a straight horizontal cut), while diacritics are
        still captured via the vertical dilation.
        """
        if not polygons:
            return []

        H, W = image.shape[:2]
        padding_ratio = self.settings.get("diacritic_padding_ratio", 0.25)
        line_images: list[np.ndarray] = []

        for polygon in polygons:
            pts = np.asarray(polygon, dtype=np.int32).reshape((-1, 2))
            x, y, w, h = cv2.boundingRect(pts)

            if w <= 0 or h <= 0:
                continue

            # ── Step 1: polygon mask (follows the curve) ─────────────── #
            mask = np.zeros((H, W), dtype=np.uint8)
            cv2.fillPoly(mask, [pts], 255)

            # ── Step 2: dilate mask vertically for diacritic padding ──── #
            # A rectangular kernel of width=1, height=(2*v_pad+1) expands
            # the mask above and below while preserving horizontal contours.
            v_pad = max(1, int(h * padding_ratio))
            vkernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 2 * v_pad + 1))
            mask_padded = cv2.dilate(mask, vkernel)

            # ── Step 3: apply mask and crop ───────────────────────────── #
            # Find tight bounding box of the expanded mask
            ys, xs = np.where(mask_padded > 0)
            if len(xs) == 0 or len(ys) == 0:
                continue

            y_top = max(0, int(ys.min()))
            y_bot = min(H, int(ys.max()) + 1)
            x_left = max(0, int(xs.min()))
            x_right = min(W, int(xs.max()) + 1)

            # Crop both image and mask to the padded bounding box
            region = image[y_top:y_bot, x_left:x_right].copy()
            mask_crop = mask_padded[y_top:y_bot, x_left:x_right]

            # Set pixels outside the dilated polygon to white
            region[mask_crop == 0] = 255

            line_images.append(region)

        return line_images
