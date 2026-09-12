import { base64ToDataUrl } from '../api/client';

/**
 * Syllable grouping visualization (verifikasi aturan transliterasi).
 *
 * Untuk setiap baris, menampilkan tiap SUKU KATA sebagai satu kartu:
 *   [crop huruf 1] [crop huruf 2] ...  →  "suku kata"
 *   + penjelasan aturan (rule) yang membentuknya.
 *
 * Tujuannya: melihat karakter mana saja yang SALING MEMPENGARUHI
 * (aksara dasar + gantungan/pangangge) dan menjadi bunyi apa, sehingga
 * benar/tidaknya aturan transliterasi dapat diperiksa dengan mudah.
 */
export default function SyllableGroupsView({ lines }) {
  if (!lines || lines.length === 0) return null;

  return (
    <div id="syllable-groups-view">
      <p className="text-dark-text-muted text-xs mb-3">
        Pengelompokan karakter yang <span className="text-accent-gold">saling mempengaruhi</span> menjadi
        satu suku kata. Setiap kartu menampilkan glyph penyusun (aksara dasar + gantungan/pangangge),
        bunyi yang dihasilkan, dan aturan (R1–R7) yang berlaku. Berguna untuk memverifikasi
        kebenaran aturan transliterasi.
      </p>

      <div className="space-y-5">
        {lines.map((line) => {
          const syllables = line.syllables || [];
          // Rangkai kata: gabungkan bunyi, pisahkan pada tanda baca.
          const reading = syllables.map((s) => s.text).join('');

          return (
            <div key={line.line_index} className="border border-dark-border rounded-lg bg-dark-card/40 overflow-hidden">
              {/* Header baris */}
              <div className="flex items-center gap-3 px-3 py-2 border-b border-dark-border bg-dark-card/60">
                <span className="text-xs font-mono text-accent-teal">Baris {line.line_index + 1}</span>
                <span className="detection-badge ml-auto">{syllables.length} suku kata</span>
              </div>

              {syllables.length === 0 ? (
                <p className="px-3 py-3 text-xs text-dark-text-muted italic">
                  Tidak ada suku kata terbentuk pada baris ini.
                </p>
              ) : (
                <>
                  {/* Rangkaian kartu suku kata */}
                  <div className="flex flex-wrap items-stretch gap-2 p-3">
                    {syllables.map((syl, sIdx) => (
                      <SyllableCard key={sIdx} syllable={syl} index={sIdx} lineIndex={line.line_index} />
                    ))}
                  </div>

                  {/* Bacaan gabungan baris */}
                  <div className="px-3 pb-3">
                    <div className="rounded-lg border border-accent-teal/20 bg-accent-teal/5 px-3 py-2">
                      <span className="text-[10px] uppercase tracking-wide text-dark-text-muted mr-2">
                        Bacaan baris
                      </span>
                      <span className="font-mono text-sm text-accent-teal" id={`syllable-reading-${line.line_index}`}>
                        {reading || '—'}
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend aturan */}
      <div className="mt-4 p-3 rounded-lg border border-dark-border/50 bg-dark-card/30">
        <p className="text-[10px] text-dark-text-muted leading-relaxed">
          <span className="text-accent-gold font-medium">Keterangan aturan:</span>{' '}
          <span className="text-dark-text">R1</span> vokal inheren /a/ ·{' '}
          <span className="text-dark-text">R2</span> pangangge suara (ulu/suku/taling/tedong/pepet) ·{' '}
          <span className="text-dark-text">R3</span> gantungan (gugus konsonan) ·{' '}
          <span className="text-dark-text">R4</span> pangangge tengenan (cecek/surang/bisah) ·{' '}
          <span className="text-dark-text">R5</span> adeg-adeg (vokal mati) ·{' '}
          <span className="text-dark-text">R6</span> aksara vokalik ·{' '}
          <span className="text-dark-text">R7</span> tanda baca.
        </p>
      </div>
    </div>
  );
}

/**
 * Satu kartu suku kata: glyph penyusun → bunyi + aturan.
 */
function SyllableCard({ syllable, index, lineIndex }) {
  const isPunct = !syllable.text.trim(); // ", " dsb
  const glyphs = syllable.glyphs || [];

  return (
    <div
      className="flex flex-col rounded-lg border border-dark-border bg-dark-card min-w-[92px] max-w-[220px]"
      id={`syllable-${lineIndex}-${index}`}
      title={syllable.rule}
    >
      {/* Glyph penyusun */}
      <div className="flex flex-wrap items-center justify-center gap-1 p-2 border-b border-dark-border/60">
        {glyphs.length === 0 && (
          <span className="text-[10px] text-dark-text-muted italic px-1">tanda baca</span>
        )}
        {glyphs.map((g, gi) => (
          <div key={gi} className="flex flex-col items-center gap-0.5">
            {g.crop_image ? (
              <div className="w-9 h-9 rounded overflow-hidden border border-dark-border bg-white flex items-center justify-center">
                <img
                  src={base64ToDataUrl(g.crop_image)}
                  alt={g.class_name}
                  className="w-full h-full object-contain"
                  loading="lazy"
                />
              </div>
            ) : (
              <div className="w-9 h-9 rounded border border-dashed border-dark-border flex items-center justify-center text-[9px] text-dark-text-muted">
                {g.class_id}
              </div>
            )}
            <span
              className="text-[9px] font-mono text-dark-text-muted leading-tight text-center max-w-[54px] truncate"
              title={g.class_name}
            >
              {g.class_name}
            </span>
          </div>
        ))}
      </div>

      {/* Bunyi hasil */}
      <div className="flex items-center justify-center py-1.5 bg-accent-gold/5">
        <span className="text-[9px] text-dark-text-muted mr-1">→</span>
        <span className="font-mono text-base font-semibold text-accent-gold">
          {isPunct ? '⟨jeda⟩' : syllable.text}
        </span>
      </div>

      {/* Aturan */}
      {syllable.rule && (
        <div className="px-2 py-1.5 border-t border-dark-border/60">
          <p className="text-[9px] text-dark-text-muted leading-snug">{syllable.rule}</p>
        </div>
      )}
    </div>
  );
}
