/**
 * Processing status with animated loading indicator.
 */
export default function ProcessingStatus({ stage }) {
  return (
    <div className="glass-card p-6 animate-fade-in" id="processing-status">
      <div className="flex items-center gap-4">
        {/* Spinner */}
        <div className="relative w-12 h-12 flex-shrink-0">
          <div className="absolute inset-0 rounded-full border-2 border-dark-border" />
          <div className="absolute inset-0 rounded-full border-2 border-accent-gold border-t-transparent animate-spin" />
          <div className="absolute inset-2 rounded-full border-2 border-accent-teal/40 border-b-transparent animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
        </div>

        <div className="flex-1">
          <p className="text-dark-text font-medium">Memproses naskah lontar...</p>
          <p className="text-dark-text-muted text-sm mt-0.5">{stage}</p>
        </div>
      </div>

      {/* Progress steps */}
      <div className="mt-5 grid grid-cols-4 gap-2">
        {[
          { label: 'Segmentasi', icon: '🔲' },
          { label: 'Deteksi', icon: '🔍' },
          { label: 'Analisis', icon: '📐' },
          { label: 'Transliterasi', icon: '📝' },
        ].map((step, i) => (
          <div key={step.label} className="flex flex-col items-center gap-1.5">
            <div className="shimmer w-full h-1.5 rounded-full" style={{ animationDelay: `${i * 0.3}s` }} />
            <span className="text-xs text-dark-text-muted">{step.icon} {step.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
