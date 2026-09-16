/**
 * Final transliteration output (always visible, not collapsible).
 */
export default function TransliterationView({
  lines,
  fullBalineseUnicode,
  fullTransliteration,
}) {
  return (
    <div className="glass-card p-5 animate-pulse-glow" id="transliteration-display">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">📝</span>
        <h3 className="text-sm font-semibold text-dark-text">Hasil Transliterasi</h3>
      </div>

      {/* Full Unicode and Latin output */}
      <div className="transliteration-output mb-4" id="full-transliteration">
        <p className="text-xs text-dark-text-muted mb-2 font-medium">Aksara Bali:</p>
        <p
          className="balinese-unicode text-dark-text leading-relaxed whitespace-pre-wrap"
          lang="ban-Bali"
        >
          {fullBalineseUnicode || '—'}
        </p>
        <div className="my-4 border-t border-dark-border/70" />
        <p className="text-xs text-dark-text-muted mb-2 font-medium">Transliterasi Lengkap:</p>
        <p className="text-accent-gold text-lg leading-relaxed font-mono">
          {fullTransliteration || '—'}
        </p>
      </div>

      {/* Per-line breakdown */}
      {lines && lines.length > 0 && (
        <div>
          <p className="text-xs text-dark-text-muted mb-2 font-medium">Per Baris:</p>
          <div className="space-y-2">
            {lines.map((line) => (
              <div
                key={line.line_index}
                className="flex items-start gap-3 p-3 rounded-lg border border-dark-border/50 bg-dark-card/30"
                id={`transliteration-line-${line.line_index}`}
              >
                <span className="text-xs font-mono text-accent-teal flex-shrink-0 mt-0.5">
                  {line.line_index + 1}
                </span>
                <div className="min-w-0">
                  <p
                    className="balinese-unicode text-dark-text leading-relaxed break-words"
                    lang="ban-Bali"
                  >
                    {line.balinese_unicode || '—'}
                  </p>
                  <p className="font-mono text-sm text-accent-gold/90 leading-relaxed break-words mt-1">
                    {line.transliteration || '—'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
