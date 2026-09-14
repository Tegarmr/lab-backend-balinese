"""
YOLO-based character detection service.

Wraps Ultralytics YOLO model for detecting individual Balinese
aksara characters within segmented text line images.
"""

import logging

import cv2
import numpy as np
from ultralytics import YOLO

from app.config import (
    YOLO_AGNOSTIC_NMS,
    YOLO_CONF_THRESHOLD,
    YOLO_DEDUP_IOU,
    YOLO_IMG_SIZE,
    YOLO_IOU_THRESHOLD,
    YOLO_MAX_DET,
)

logger = logging.getLogger(__name__)

# ── 55 Character Classes ──────────────────────────────────
# Mapping from class ID to aksara name (from karakter_bali.md)
CLASS_MAP = {
    0: "ha",
    1: "na",
    2: "ca",
    3: "ra",
    4: "ka",
    5: "da",
    6: "ta",
    7: "sa",
    8: "wa",
    9: "la",
    10: "ma",
    11: "ga",
    12: "ba",
    13: "nga",
    14: "pa",
    15: "ja",
    16: "ya",
    17: "nya",
    18: "Gantungan ha",
    19: "Gantungan na",
    20: "Gantungan ca",
    21: "Gantungan ra",
    22: "Gantungan da",
    23: "Gantungan ta",
    24: "Gantungan sa",
    25: "Gantungan wa",
    26: "Gantungan la",
    27: "Gantungan ma",
    28: "Gantungan ga",
    29: "Gantungan ba",
    30: "Gantungan nga",
    31: "Gantungan pa",
    32: "Gantungan ja",
    33: "Gantungan ya",
    34: "Gantungan nya",
    35: "Tedong",
    36: "ulu",
    37: "suku",
    38: "taleng",
    39: "pepet",
    40: "cecek",
    41: "surang",
    42: "bisah",
    43: "adeg-adeg",
    44: "titik",
    45: "A kara",
    46: "I kara",
    47: "U kara",
    48: "sa saga",
    49: "na rambat",
    50: "da madu",
    51: "la lenga",
    52: "Gantungan da madu",
    53: "Gantungan ra repa",
    54: "Gantungan ta tawa",
}


class YOLODetectionService:
    """YOLO character detection service."""

    _instance = None

    def __init__(self, weights_path: str, device: str = "cpu"):
        self.device = device
        logger.info("Loading YOLO model from: %s", weights_path)
        self.model = YOLO(weights_path)
        self.class_names = CLASS_MAP
        logger.info("YOLO model loaded on device: %s", device)

    @classmethod
    def get_instance(cls, weights_path: str, device: str = "cpu"):
        """Singleton pattern to avoid loading the model multiple times."""
        if cls._instance is None:
            cls._instance = cls(weights_path, device)
        return cls._instance

    def detect_line(
        self,
        line_image: np.ndarray,
        conf: float = None,
        iou: float = None,
    ) -> list[dict]:
        """
        Detect characters in a single line image.

        Args:
            line_image: BGR image of a single text line.
            conf: Confidence threshold (default from config).
            iou: IoU threshold for NMS (default from config).

        Returns:
            List of detection dicts sorted by x_center (left to right).
        """
        if conf is None:
            conf = YOLO_CONF_THRESHOLD
        if iou is None:
            iou = YOLO_IOU_THRESHOLD

        results = self.model.predict(
            line_image,
            imgsz=YOLO_IMG_SIZE,
            conf=conf,
            iou=iou,
            agnostic_nms=YOLO_AGNOSTIC_NMS,
            max_det=YOLO_MAX_DET,
            device=self.device,
            verbose=False,
        )

        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                # Drop low-confidence detections (defensive: predict() already
                # filters by `conf`, this guards against callers passing a
                # lower threshold or float rounding at the boundary).
                if confidence < conf:
                    continue

                # Get box coordinates (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x_center = (x1 + x2) / 2
                y_center = (y1 + y2) / 2
                width = x2 - x1
                height = y2 - y1

                class_name = self.class_names.get(class_id, f"class_{class_id}")

                detections.append(
                    {
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": round(confidence, 4),
                        "x1": round(float(x1), 2),
                        "y1": round(float(y1), 2),
                        "x2": round(float(x2), 2),
                        "y2": round(float(y2), 2),
                        "x_center": round(float(x_center), 2),
                        "y_center": round(float(y_center), 2),
                        "width": round(float(width), 2),
                        "height": round(float(height), 2),
                    }
                )

        detections = self._dedup_overlaps(
            detections, YOLO_DEDUP_IOU, agnostic=YOLO_AGNOSTIC_NMS
        )

        # Sort by x_center (left-to-right reading order)
        detections.sort(key=lambda d: d["x_center"])
        return detections

    @staticmethod
    def _iou(a: dict, b: dict) -> float:
        """Intersection-over-union of two detection boxes (xyxy)."""
        ax1, ay1, ax2, ay2 = a["x1"], a["y1"], a["x2"], a["y2"]
        bx1, by1, bx2, by2 = b["x1"], b["y1"], b["x2"], b["y2"]

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter = inter_w * inter_h
        if inter <= 0:
            return 0.0

        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    @classmethod
    def _dedup_overlaps(
        cls, detections: list[dict], iou_thr: float, agnostic: bool = False
    ) -> list[dict]:
        """
        Greedy NMS, preserving different classes unless explicitly agnostic.

        Sorts by confidence (highest first) and drops any lower-confidence box
        that overlaps an already-kept box of the same class by more than
        ``iou_thr``. Combining marks can overlap a base letter legitimately.
        """
        ordered = sorted(detections, key=lambda d: d["confidence"], reverse=True)
        kept: list[dict] = []
        for det in ordered:
            if any(
                (agnostic or det["class_id"] == k["class_id"])
                and cls._iou(det, k) > iou_thr
                for k in kept
            ):
                continue
            kept.append(det)
        return kept

    def detect_all_lines(self, line_images: list[np.ndarray]) -> list[list[dict]]:
        """
        Process all segmented lines and return detections per line.

        Args:
            line_images: List of BGR line images.

        Returns:
            List of detection lists, one per line.
        """
        all_detections = []
        for i, line_img in enumerate(line_images):
            dets = self.detect_line(line_img)
            logger.info("Line %d: %d characters detected", i + 1, len(dets))
            all_detections.append(dets)
        return all_detections
