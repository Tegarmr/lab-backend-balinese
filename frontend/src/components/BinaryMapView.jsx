import { base64ToDataUrl } from '../api/client';

/**
 * Binary map visualization (SeamFormer Stage 1)
 */
export default function BinaryMapView({ base64Image }) {
  if (!base64Image) return null;

  return (
    <div id="binary-map-view">
      <p className="text-dark-text-muted text-xs mb-3">
        Binary map menunjukkan area teks yang terdeteksi oleh model SeamFormer.
        Piksel putih menandakan area teks, piksel hitam menandakan background.
      </p>
      <div className="rounded-lg overflow-hidden border border-dark-border bg-dark-card">
        <img
          src={base64ToDataUrl(base64Image)}
          alt="Binary map hasil segmentasi"
          className="w-full h-auto object-contain max-h-[400px]"
          loading="lazy"
          id="binary-map-image"
        />
      </div>
    </div>
  );
}
