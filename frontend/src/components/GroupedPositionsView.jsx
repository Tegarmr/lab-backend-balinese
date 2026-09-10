/**
 * Grouped positions visualization.
 * Shows the (vertical-group) notation format where characters
 * at the same x-position are grouped in parentheses.
 */
export default function GroupedPositionsView({ lines }) {
  if (!lines || lines.length === 0) return null;

  return (
    <div id="grouped-positions-view">
      <p className="text-dark-text-muted text-xs mb-3">
        Format pengelompokan posisi karakter. Karakter dalam tanda kurung <code className="text-accent-teal">()</code> berada
        pada posisi x yang sama (bertumpuk vertikal), menandakan aksara dasar dengan pengangge/gantungan.
      </p>

      <div className="space-y-3">
        {lines.map((line) => (
          <div key={line.line_index} className="p-4 rounded-lg border border-dark-border bg-dark-card">
            <div className="flex items-start gap-3">
              <span className="text-xs font-mono text-accent-teal flex-shrink-0 mt-0.5">
                Baris {line.line_index + 1}
              </span>
              <div className="flex-1 min-w-0">
                <p className="font-mono text-sm text-dark-text break-all leading-relaxed" id={`grouped-text-${line.line_index}`}>
                  {renderGroupedText(line.grouped_text)}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-4 p-3 rounded-lg border border-dark-border/50 bg-dark-card/30">
        <p className="text-[10px] text-dark-text-muted">
          <span className="text-accent-gold font-medium">Keterangan:</span>{' '}
          Angka di luar kurung = karakter tunggal pada posisi x unik.{' '}
          Angka dalam kurung = karakter bertumpuk vertikal (misal: aksara dasar + pengangge/gantungan).
        </p>
      </div>
    </div>
  );
}

/**
 * Render grouped text with syntax highlighting.
 */
function renderGroupedText(text) {
  if (!text) return <span className="text-dark-text-muted italic">Tidak ada data</span>;

  // Split by spaces and highlight parenthesized groups
  return text.split(' ').map((part, idx) => {
    const isGroup = part.startsWith('(') && part.endsWith(')');
    return (
      <span key={idx}>
        {idx > 0 && <span className="text-dark-text-muted mx-0.5">·</span>}
        {isGroup ? (
          <span className="text-accent-gold bg-accent-gold/5 px-0.5 rounded">
            {part}
          </span>
        ) : (
          <span className="text-dark-text">{part}</span>
        )}
      </span>
    );
  });
}
