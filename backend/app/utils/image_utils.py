"""
Image utility functions: encoding, resizing, color conversion.
"""

import base64
import cv2
import numpy as np

from app.config import JPEG_QUALITY, MAX_IMAGE_DIMENSION


def encode_image_to_base64(image: np.ndarray, fmt: str = ".jpg") -> str:
    """Encode a BGR/grayscale numpy image to a base64 string."""
    if fmt == ".jpg":
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    else:
        encode_params = []

    success, buffer = cv2.imencode(fmt, image, encode_params)
    if not success:
        raise ValueError("Failed to encode image")
    return base64.b64encode(buffer).decode("utf-8")


def resize_if_needed(image: np.ndarray, max_dim: int = MAX_IMAGE_DIMENSION) -> np.ndarray:
    """Resize image so its largest dimension does not exceed max_dim."""
    h, w = image.shape[:2]
    if max(h, w) <= max_dim:
        return image
    scale = max_dim / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def draw_detections_on_image(
    image: np.ndarray,
    detections: list,
    color: tuple = (0, 255, 0),
    thickness: int = 2
) -> np.ndarray:
    """Draw bounding boxes and labels on an image."""
    result = image.copy()
    for det in detections:
        x1 = int(det["x_center"] - det["width"] / 2)
        y1 = int(det["y_center"] - det["height"] / 2)
        x2 = int(det["x_center"] + det["width"] / 2)
        y2 = int(det["y_center"] + det["height"] / 2)

        cv2.rectangle(result, (x1, y1), (x2, y2), color, thickness)

        label = f'{det["class_name"]} {det["confidence"]:.2f}'
        font_scale = 0.4
        font_thickness = 1
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)

        cv2.rectangle(result, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(
            result, label, (x1 + 2, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX, font_scale,
            (0, 0, 0), font_thickness, cv2.LINE_AA
        )
    return result


def crop_detection(image: np.ndarray, det: dict, padding: int = 2) -> np.ndarray:
    """Crop a detection region from the image with optional padding."""
    h, w = image.shape[:2]
    x1 = max(0, int(det["x_center"] - det["width"] / 2) - padding)
    y1 = max(0, int(det["y_center"] - det["height"] / 2) - padding)
    x2 = min(w, int(det["x_center"] + det["width"] / 2) + padding)
    y2 = min(h, int(det["y_center"] + det["height"] / 2) + padding)
    return image[y1:y2, x1:x2]
