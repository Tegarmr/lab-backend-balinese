/**
 * Header component with app branding.
 */
export default function Header() {
  return (
    <header className="relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-primary-900/30 via-dark-bg to-surface-900/20" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--color-accent-gold)_0%,_transparent_50%)] opacity-5" />

      <div className="relative max-w-6xl mx-auto px-4 py-8 sm:py-10">
        <div className="flex items-center gap-4">
          {/* Icon */}
          <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-gradient-to-br from-accent-gold/20 to-primary-700/20 border border-accent-gold/30 flex items-center justify-center animate-pulse-glow">
            <span className="text-2xl sm:text-3xl">🏛️</span>
          </div>

          {/* Title */}
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              <span className="bg-gradient-to-r from-accent-gold to-accent-amber bg-clip-text text-transparent">
                Deep
              </span>
              <span className="text-dark-text">Lontar</span>
            </h1>
            <p className="text-sm text-dark-text-muted mt-0.5">
              Transliterasi Aksara Lontar Bali → Alfabet Latin
            </p>
          </div>
        </div>

        {/* Subtitle description */}
        <p className="mt-4 text-sm text-dark-text-muted max-w-2xl leading-relaxed">
          Unggah foto naskah lontar Bali untuk mendapatkan transliterasi otomatis.
          Sistem menggunakan <span className="text-accent-teal font-medium">SeamFormer</span> untuk segmentasi baris
          dan <span className="text-accent-teal font-medium">YOLOv8</span> untuk deteksi karakter aksara.
        </p>
      </div>
    </header>
  );
}
