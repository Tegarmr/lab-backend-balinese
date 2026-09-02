"""
Transliteration API router.

POST /api/transliterate — accepts an image file, runs the full pipeline,
and returns all intermediate + final results.
"""

import gc
import logging
import os
import time
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import (
    ALLOWED_EXTENSIONS,
    DEVICE,
    MAX_IMAGE_SIZE,
    SEAMFORMER_WEIGHTS,
    UPLOAD_DIR,
    YOLO_WEIGHTS,
)
from app.models.schemas import (
    DetectionItem,
    LineResult,
    PositionItem,
    TransliterationResponse,
)
from app.services.detection import YOLODetectionService
from app.services.segmentation import SeamFormerService
from app.services.transliteration import TransliterationEngine
from app.utils.image_utils import (
    crop_detection,
    draw_detections_on_image,
    encode_image_to_base64,
    resize_if_needed,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["transliteration"])


@router.post("/transliterate", response_model=TransliterationResponse)
async def transliterate(file: UploadFile = File(...)):
    """
    Full transliteration pipeline.

    Accepts a lontar manuscript image and returns:
    - Input image
    - Binary map (SeamFormer Stage 1)
    - Scribble map (SeamFormer Stage 1)
    - Segmented line images
    - YOLO detections per line (with character crops)
    - Character positions (x, y)
    - Grouped position text (vertical stacking notation)
    - Final transliteration
    """
    start_time = time.time()

    # ── Validate file ─────────────────────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # ── Save uploaded file ────────────────────────────────
    file_id = uuid.uuid4().hex[:12]
    save_path = str(UPLOAD_DIR / f"{file_id}{ext}")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max: {MAX_IMAGE_SIZE // (1024*1024)}MB",
        )

    with open(save_path, "wb") as f:
        f.write(content)

    logger.info("Saved upload: %s (%d bytes)", save_path, len(content))

    try:
        # ── Stage 1 & 2: SeamFormer Segmentation ─────────
        logger.info("Starting segmentation...")
        seg_service = SeamFormerService.get_instance(
            str(SEAMFORMER_WEIGHTS), DEVICE
        )
        seg_result = seg_service.process(save_path)

        import cv2
        original_image = cv2.imread(save_path)
        original_image = resize_if_needed(original_image)

        # Encode intermediate images
        input_image_b64 = encode_image_to_base64(original_image)
        binary_map_b64 = encode_image_to_base64(seg_result.binary_map)
        scribble_map_b64 = encode_image_to_base64(seg_result.scribble_map)
        segmentation_image_b64 = encode_image_to_base64(seg_result.segmentation_vis)

        # Encode segmented line images
        segmented_lines_b64 = [
            encode_image_to_base64(line_img)
            for line_img in seg_result.line_images
        ]

        logger.info("Segmentation complete: %d lines", len(seg_result.line_images))

        if len(seg_result.line_images) == 0:
            # No lines detected — return early
            elapsed = time.time() - start_time
            return TransliterationResponse(
                input_image=input_image_b64,
                binary_map=binary_map_b64,
                scribble_map=scribble_map_b64,
                segmentation_image=segmentation_image_b64,
                segmented_lines=[],
                lines=[],
                full_transliteration="(Tidak ada baris teks terdeteksi)",
                processing_time=round(elapsed, 2),
                total_lines=0,
                total_characters=0,
            )

        # ── Stage 3: YOLO Detection ──────────────────────
        logger.info("Starting YOLO detection...")
        det_service = YOLODetectionService.get_instance(
            str(YOLO_WEIGHTS), DEVICE
        )
        all_detections = det_service.detect_all_lines(seg_result.line_images)

        # ── Stage 4: Transliteration ─────────────────────
        logger.info("Starting transliteration...")
        trans_engine = TransliterationEngine()
        transliterations, grouped_texts, positions_per_line = (
            trans_engine.transliterate_all_lines(all_detections)
        )

        # ── Build Response ────────────────────────────────
        line_results = []
        total_chars = 0

        for i, (line_img, dets) in enumerate(
            zip(seg_result.line_images, all_detections)
        ):
            total_chars += len(dets)

            # Draw detections on line image
            det_vis = draw_detections_on_image(line_img, dets)
            det_vis_b64 = encode_image_to_base64(det_vis)

            # Crop individual character images
            detection_items = []
            for det in dets:
                crop = crop_detection(line_img, det)
                crop_b64 = encode_image_to_base64(crop) if crop.size > 0 else ""
                detection_items.append(DetectionItem(
                    class_id=det["class_id"],
                    class_name=det["class_name"],
                    confidence=det["confidence"],
                    x_center=det["x_center"],
                    y_center=det["y_center"],
                    width=det["width"],
                    height=det["height"],
                    crop_image=crop_b64,
                ))

            # Positions
            position_items = [
                PositionItem(**p) for p in positions_per_line[i]
            ]

            line_results.append(LineResult(
                line_index=i,
                line_image=segmented_lines_b64[i],
                detection_image=det_vis_b64,
                detections=detection_items,
                positions=position_items,
                grouped_text=grouped_texts[i],
                transliteration=transliterations[i],
            ))

        # Full transliteration (join all lines)
        full_trans = " / ".join(
            t for t in transliterations if t.strip()
        )

        elapsed = time.time() - start_time
        logger.info(
            "Pipeline complete: %d lines, %d chars, %.2fs",
            len(line_results), total_chars, elapsed,
        )

        return TransliterationResponse(
            input_image=input_image_b64,
            binary_map=binary_map_b64,
            scribble_map=scribble_map_b64,
            segmentation_image=segmentation_image_b64,
            segmented_lines=segmented_lines_b64,
            lines=line_results,
            full_transliteration=full_trans,
            processing_time=round(elapsed, 2),
            total_lines=len(line_results),
            total_characters=total_chars,
        )

    except Exception as e:
        logger.exception("Pipeline error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup uploaded file
        try:
            os.remove(save_path)
        except OSError:
            pass
        gc.collect()
