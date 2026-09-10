import { useState } from 'react';
import { base64ToDataUrl } from '../api/client';

/**
 * YOLO detection visualization per line.
 * Shows detection image + individual character crops with confidence.
 */
export default function YoloDetectionView({ lines }) {
  const [expandedLine, setExpandedLine] = useState(null);

  if (!lines || lines.length === 0) return null;

  return (
    <div id="yolo-detection-view">
      <p className="text-dark-text-muted text-xs mb-3">
        Hasil deteksi karakter aksara Bali menggunakan YOLOv8s.
        Setiap bounding box menunjukkan karakter yang terdeteksi beserta confidence score.
      </p>

      <div className="space-y-4">
        {lines.map((line) => (
          <div key={line.line_index} className="border border-dark-border rounded-lg overflow-hidden bg-dark-card/50">
            {/* Line header with detection image */}
            <button
              className="w-full text-left p-3 flex items-center gap-3 hover:bg-dark-card-hover transition-colors"
              onClick={() => setExpandedLine(expandedLine === line.line_index ? null : line.line_index)}
              id={`yolo-line-${line.line_index}-toggle`}
            >
              <svg
                className={`w-3 h-3 text-dark-text-muted transition-transform duration-200 flex-shrink-0 ${
                  expandedLine === line.line_index ? 'rotate-90' : ''
                }`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
              <span className="text-xs font-mono text-accent-teal">Baris {line.line_index + 1}</span>
              <span className="detection-badge ml-auto">{line.detections.length} karakter</span>
            </button>

            {/* Detection visualization image */}
            <div className="px-3 pb-2">
              <div className="rounded overflow-hidden border border-dark-border">
                <img
                  src={base64ToDataUrl(line.detection_image)}
                  alt={`Deteksi baris ${line.line_index + 1}`}
                  className="w-full h-auto object-contain max-h-[150px]"
                  loading="lazy"
                  id={`yolo-detection-img-${line.line_index}`}
                />
              </div>
            </div>

            {/* Expanded: individual character crops */}
            {expandedLine === line.line_index && (
              <div className="px-3 pb-3 animate-fade-in">
                <p className="text-xs text-dark-text-muted mb-2 font-medium">Karakter terdeteksi:</p>
                <div className="flex flex-wrap gap-2">
                  {line.detections.map((det, detIdx) => (
                    <div
                      key={detIdx}
                      className="flex flex-col items-center gap-1 p-2 rounded-lg border border-dark-border bg-dark-card hover:border-accent-teal/30 transition-colors group"
                      id={`detection-${line.line_index}-${detIdx}`}
                    >
                      {/* Character crop */}
                      {det.crop_image && (
                        <div className="w-10 h-10 rounded overflow-hidden border border-dark-border bg-white flex items-center justify-center">
                          <img
                            src={base64ToDataUrl(det.crop_image)}
                            alt={det.class_name}
                            className="w-full h-full object-contain"
                            loading="lazy"
                          />
                        </div>
                      )}
                      {/* Class name */}
                      <span className="text-[10px] font-mono text-accent-gold leading-tight text-center max-w-[60px] truncate" title={det.class_name}>
                        {det.class_name}
                      </span>
                      {/* Confidence */}
                      <span className="text-[9px] font-mono text-dark-text-muted">
                        {(det.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
