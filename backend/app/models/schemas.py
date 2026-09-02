"""
Pydantic models for API request/response schemas.
"""

from pydantic import BaseModel


class DetectionItem(BaseModel):
    """Single character detection from YOLO."""
    class_id: int
    class_name: str
    confidence: float
    x_center: float
    y_center: float
    width: float
    height: float
    crop_image: str  # base64 encoded cropped character


class PositionItem(BaseModel):
    """Character position in the line."""
    class_id: int
    class_name: str
    x: float
    y: float


class LineResult(BaseModel):
    """Results for a single segmented text line."""
    line_index: int
    line_image: str  # base64 encoded line image
    detection_image: str  # base64 encoded line with drawn detections
    detections: list[DetectionItem]
    positions: list[PositionItem]
    grouped_text: str  # e.g. "(321)439289(213)" format
    transliteration: str


class TransliterationResponse(BaseModel):
    """Full response for transliteration endpoint."""
    input_image: str  # base64
    binary_map: str  # base64
    scribble_map: str  # base64
    segmentation_image: str  # base64 (original with polygon overlays)
    segmented_lines: list[str]  # base64 list of cropped lines
    lines: list[LineResult]
    full_transliteration: str
    processing_time: float  # seconds
    total_lines: int
    total_characters: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    seamformer_loaded: bool
    yolo_loaded: bool
    device: str
