import { base64ToDataUrl } from '../api/client';

/**
 * Segmented lines visualization (extracted line crops).
 */
export default function SegmentedLinesView({ segmentationImage, segmentedLines }) {
  return (
    <div id="segmented-lines-view">
      <p className="text-dark-text-muted text-xs mb-3">
        Hasil segmentasi menggunakan seam-conditioned polygon. Tiap baris teks dipotong
        berdasarkan polygon mask yang dihasilkan dari binary map dan scribble map.
      </p>

      {/* Full segmentation visualization */}
      {segmentationImage && (
        <div className="mb-4">
          <p className="text-xs text-accent-teal font-medium mb-2">Visualisasi Polygon Segmentasi</p>
          <div className="rounded-lg overflow-hidden border border-dark-border bg-dark-card">
            <img
              src={base64ToDataUrl(segmentationImage)}
              alt="Visualisasi segmentasi dengan polygon"
              className="w-full h-auto object-contain max-h-[400px]"
              loading="lazy"
              id="segmentation-vis-image"
            />
          </div>
        </div>
      )}

      {/* Individual line crops */}
      {segmentedLines && segmentedLines.length > 0 && (
        <div>
          <p className="text-xs text-accent-teal font-medium mb-2">
            Baris Teks Tersegmentasi ({segmentedLines.length} baris)
          </p>
          <div className="space-y-2">
            {segmentedLines.map((line, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <span className="text-xs text-dark-text-muted font-mono w-12 flex-shrink-0 text-right">
                  Line {idx + 1}
                </span>
                <div className="flex-1 rounded-lg overflow-hidden border border-dark-border bg-dark-card">
                  <img
                    src={base64ToDataUrl(line)}
                    alt={`Baris teks ${idx + 1}`}
                    className="w-full h-auto object-contain max-h-[100px]"
                    loading="lazy"
                    id={`segmented-line-${idx}`}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
