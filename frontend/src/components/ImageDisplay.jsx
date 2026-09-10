import { base64ToDataUrl } from '../api/client';

/**
 * Input image display (always visible, not collapsible).
 */
export default function ImageDisplay({ base64Image }) {
  if (!base64Image) return null;

  return (
    <div className="glass-card p-5" id="input-image-display">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">📷</span>
        <h3 className="text-sm font-semibold text-dark-text">Gambar Input Naskah</h3>
      </div>
      <div className="rounded-lg overflow-hidden border border-dark-border bg-dark-card">
        <img
          src={base64ToDataUrl(base64Image)}
          alt="Input naskah lontar Bali"
          className="w-full h-auto object-contain max-h-[500px]"
          loading="lazy"
          id="input-image"
        />
      </div>
    </div>
  );
}
