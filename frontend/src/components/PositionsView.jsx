/**
 * Character positions table (x, y coordinates).
 */
export default function PositionsView({ lines }) {
  if (!lines || lines.length === 0) return null;

  return (
    <div id="positions-view">
      <p className="text-dark-text-muted text-xs mb-3">
        Posisi setiap karakter yang terdeteksi dalam koordinat (x, y) pada gambar baris.
        Koordinat x menentukan urutan baca (kiri ke kanan), y menentukan posisi vertikal.
      </p>

      <div className="space-y-4">
        {lines.map((line) => (
          <div key={line.line_index}>
            <p className="text-xs font-mono text-accent-teal mb-2">Baris {line.line_index + 1}</p>
            <div className="overflow-x-auto rounded-lg border border-dark-border">
              <table className="w-full text-xs" id={`positions-table-${line.line_index}`}>
                <thead>
                  <tr className="bg-dark-card border-b border-dark-border">
                    <th className="px-3 py-2 text-left text-dark-text-muted font-medium">#</th>
                    <th className="px-3 py-2 text-left text-dark-text-muted font-medium">ID</th>
                    <th className="px-3 py-2 text-left text-dark-text-muted font-medium">Karakter</th>
                    <th className="px-3 py-2 text-right text-dark-text-muted font-medium">X</th>
                    <th className="px-3 py-2 text-right text-dark-text-muted font-medium">Y</th>
                  </tr>
                </thead>
                <tbody>
                  {line.positions.map((pos, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-dark-border/50 hover:bg-dark-card-hover transition-colors"
                    >
                      <td className="px-3 py-1.5 text-dark-text-muted font-mono">{idx + 1}</td>
                      <td className="px-3 py-1.5 font-mono text-accent-teal">{pos.class_id}</td>
                      <td className="px-3 py-1.5 text-dark-text">{pos.class_name}</td>
                      <td className="px-3 py-1.5 text-right font-mono text-accent-gold">{pos.x.toFixed(1)}</td>
                      <td className="px-3 py-1.5 text-right font-mono text-accent-amber">{pos.y.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
