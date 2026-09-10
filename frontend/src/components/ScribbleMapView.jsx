import { base64ToDataUrl } from '../api/client';

/**
 * Scribble map visualization (SeamFormer Stage 1).
 */
export default function ScribbleMapView({ base64Image }) {
  if (!base64Image) return null;

  return (
    <div id="scribble-map-view">
      <p className="text-dark-text-muted text-xs mb-3">
        Scribble map merupakan garis panduan (scribble) untuk memisahkan tiap baris teks.
        Model SeamFormer memprediksi garis pemisah antar baris teks pada naskah lontar.
      </p>
      <div className="rounded-lg overflow-hidden border border-dark-border bg-dark-card">
        <img
          src={base64ToDataUrl(base64Image)}
          alt="Scribble map hasil segmentasi"
          className="w-full h-auto object-contain max-h-[400px]"
          loading="lazy"
          id="scribble-map-image"
        />
      </div>
    </div>
  );
}
