"""
Application configuration using environment variables.
"""

import os
from pathlib import Path

# ──| Base Paths ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
WEIGHTS_DIR = Path(os.getenv("WEIGHTS_DIR", str(BASE_DIR / "weights")))
SEAMFORMER_DIR = BASE_DIR / "seamformer"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ── Model Weights ──────────────────────────────────────────
SEAMFORMER_WEIGHTS = Path(
    os.getenv("SEAMFORMER_WEIGHTS", str(WEIGHTS_DIR / "BEST-MODEL-BL_ft_scr-8.pt"))
)
YOLO_WEIGHTS = Path(
    os.getenv("YOLO_WEIGHTS", str(WEIGHTS_DIR / "deeplontar_v8l_reliable_best.pt"))
)

# ── Device ─────────────────────────────────────────────────
DEVICE = os.getenv("DEVICE", "cpu")  # "cpu" or "cuda:0"

# ── Processing Settings ───────────────────────────────────
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", 10 * 1024 * 1024))  # 10MB
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", 2048))
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

# ── SeamFormer Settings ───────────────────────────────
SEAMFORMER_SETTINGS = {
    "encoder_layers": 6,
    "encoder_heads": 8,
    "encoder_dims": 768,
    "img_size": 256,
    "patch_size": 8,
    "split_size": 256,
    "threshold": 0.30,
    # Lontar-specific post-processing settings
    "row_separation_kernel": int(os.getenv("ROW_SEPARATION_KERNEL", "3")),
    "hull_merge_tolerance": int(os.getenv("HULL_MERGE_TOLERANCE", "15")),
    "line_merge_split_ratio": float(os.getenv("LINE_MERGE_SPLIT_RATIO", "1.8")),
    "diacritic_padding_ratio": float(os.getenv("DIACRITIC_PADDING_RATIO", "0.05")),
}

# ── YOLO Settings ─────────────────────────────────────────
# Match the fine-tuning notebook's prediction settings. A whole lontar line
# shrunk to 640 loses small strokes; 0.5 also discards many valid glyphs.
YOLO_CONF_THRESHOLD = float(os.getenv("YOLO_CONF", "0.25"))
YOLO_IOU_THRESHOLD = float(os.getenv("YOLO_IOU", "0.45"))
YOLO_IMG_SIZE = int(os.getenv("YOLO_IMG_SIZE", "1280"))
YOLO_MAX_DET = int(os.getenv("YOLO_MAX_DET", "800"))
# Preserve overlapping base letters and combining marks of different classes.
YOLO_AGNOSTIC_NMS = os.getenv("YOLO_AGNOSTIC_NMS", "false").lower() == "true"
# Duplicate suppression follows the same class policy as model NMS.
YOLO_DEDUP_IOU = float(os.getenv("YOLO_DEDUP_IOU", "0.45"))

# ── CORS ──────────────────────────────────────────────────
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")

# ── JPEG quality for intermediate images (reduces payload) ─
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "75"))

# ── Vertical grouping threshold (pixels) ──────────────────
X_GROUP_THRESHOLD = int(os.getenv("X_GROUP_THRESHOLD", "15"))

# ── Lontar Line Segmentation Fixes ───────────────────────
# Vertical morphological opening kernel size to separate tight rows in binary map
# before scribble post-processing. Set 0 to disable. (odd number, e.g. 3 or 5)
ROW_SEPARATION_KERNEL = int(os.getenv("ROW_SEPARATION_KERNEL", "3"))

# Hull merge Y-tolerance (pixels). Reduced from SeamFormer default of 30
# so tightly-spaced lontar rows are not merged into one scribble.
HULL_MERGE_TOLERANCE = int(os.getenv("HULL_MERGE_TOLERANCE", "15"))

# If a polygon's height > this ratio x median line height -> treat as merged rows
# and attempt to split using horizontal projection profile analysis.
LINE_MERGE_SPLIT_RATIO = float(os.getenv("LINE_MERGE_SPLIT_RATIO", "1.8"))

# Fractional vertical padding added above and below each line crop
# to capture diacritics (pengangge suara, gantungan) outside the polygon.
DIACRITIC_PADDING_RATIO = float(os.getenv("DIACRITIC_PADDING_RATIO", "0.25"))
