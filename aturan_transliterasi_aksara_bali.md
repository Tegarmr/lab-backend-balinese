# Aturan Transliterasi Aksara Bali → Latin

Dokumen ini menjelaskan aturan transliterasi *rule-based* (berbasis aturan)
yang dipakai oleh mesin transliterasi pada
`backend/app/services/transliteration.py`. Aturan disusun dari konvensi
**Pasang Aksara Bali** dan aturan fonologis untuk transliterasi naskah lontar,
lalu disesuaikan dengan **55 kelas karakter** keluaran model deteksi YOLO
(`deeplontar_v8l_best.pt`) yang dipakai pada proyek ini.

> Catatan: aksara Bali adalah **abugida** — setiap aksara wianjana (konsonan)
> sudah membawa vokal inheren /a/. Vokal itu dapat diganti oleh *pangangge
> suara*, dimatikan oleh *adeg-adeg*, atau hilang karena konsonan menjadi
> anggota gugus konsonan yang ditulis dengan *gantungan/gempelan*.

---

## 1. Daftar Karakter (55 Kelas)

Pemetaan `class_id` ini harus sama persis dengan `CLASS_MAP` pada
`backend/app/services/detection.py`.

### 1.1 Aksara Wianjana — 18 konsonan dasar (vokal inheren "a")

| ID | Aksara | Bunyi | ID | Aksara | Bunyi |
|----|--------|-------|----|--------|-------|
| 0  | ha  | h  | 9  | la  | l  |
| 1  | na  | n  | 10 | ma  | m  |
| 2  | ca  | c  | 11 | ga  | g  |
| 3  | ra  | r  | 12 | ba  | b  |
| 4  | ka  | k  | 13 | nga | ng |
| 5  | da  | d  | 14 | pa  | p  |
| 6  | ta  | t  | 15 | ja  | j  |
| 7  | sa  | s  | 16 | ya  | y  |
| 8  | wa  | w  | 17 | nya | ny |

Urutan ini adalah urutan **hanacaraka**: ha-na-ca-ra-ka, da-ta-sa-wa-la,
ma-ga-ba-nga-pa, ja-ya-nya.

### 1.2 Gantungan / Gempelan — konsonan gandengan (ID 18–34)

Gantungan/gempelan adalah bentuk *subjoined* (ditulis di bawah/menempel) dari
sebuah konsonan. Fungsinya **mematikan vokal inheren konsonan sebelumnya** dan
melanjutkan gugus konsonan.

| ID | Nama | Bunyi | ID | Nama | Bunyi |
|----|------|-------|----|------|-------|
| 18 | Gantungan ha | h | 27 | Gantungan ma | m |
| 19 | Gantungan na | n | 28 | Gantungan ga | g |
| 20 | Gantungan ca | c | 29 | Gantungan ba | b |
| 21 | Gantungan ra | r | 30 | Gantungan nga | ng |
| 22 | Gantungan da | d | 31 | Gantungan pa | p |
| 23 | Gantungan ta | t | 32 | Gantungan ja | j |
| 24 | Gantungan sa | s | 33 | Gantungan ya | y |
| 25 | Gantungan wa | w | 34 | Gantungan nya | ny |
| 26 | Gantungan la | l |    |      |   |

### 1.3 Pangangge Suara — penanda vokal (ID 35–39)

| ID | Nama | Posisi terhadap aksara dasar | Bunyi |
|----|------|------------------------------|-------|
| 35 | tedong | **kanan** | memanjangkan "a" → ā (ditulis "a"); bila ada **taling** di kiri → "o" |
| 36 | ulu    | **atas**  | i |
| 37 | suku   | **bawah** | u |
| 38 | taling | **kiri** (pra-aksara) | e; bila diikuti **tedong** → "o" |
| 39 | pepet  | **atas**  | e (pepet / ě, vokal pepet/schwa) |

### 1.4 Pangangge Tengenan — penanda konsonan akhir/koda (ID 40–42)

| ID | Nama | Bunyi koda |
|----|------|------------|
| 40 | cecek  | -ng |
| 41 | surang | -r  |
| 42 | bisah  | -h  |

### 1.5 Glyph struktural

| ID | Nama | Fungsi |
|----|------|--------|
| 43 | adeg-adeg | *virama* — mematikan vokal inheren (konsonan mati) |
| 44 | titik | tanda baca / pemisah (carik) → ditransliterasi sebagai ", " |

### 1.6 Aksara Suara — vokal mandiri (ID 45–47)

| ID | Nama | Bunyi |
|----|------|-------|
| 45 | A kara | a |
| 46 | I kara | i |
| 47 | U kara | u |

Aksara suara berdiri sendiri (di awal kata) dan **tidak** membawa konsonan.

### 1.7 Aksara Wayah / Sualalita — untuk kata serapan Sanskerta–Kawi (ID 48–51)

| ID | Nama | Bunyi | Keterangan |
|----|------|-------|------------|
| 48 | sa saga   | s  | varian sa (ś) |
| 49 | na rambat | n  | varian na (ṇ) |
| 50 | da madu   | d  | varian da (dh), mis. "Dharma" |
| 51 | la lenga  | **le** (lě) | **vocalic** — sudah membawa vokal pepet "e" |

> ⚠️ **la lenga (51) adalah aksara vokalik**, bukan konsonan "l" biasa. Ia
> mewakili bunyi /lə/ sehingga ditransliterasi "le", bukan "l".

### 1.8 Gantungan Wayah (ID 52–54)

| ID | Nama | Bunyi | Keterangan |
|----|------|-------|------------|
| 52 | Gantungan da madu  | d  | konsonan gandengan |
| 53 | Gantungan ra repa  | **re** (rě) | **vocalic** — membawa konsonan "r" + vokal "e" |
| 54 | Gantungan ta tawa  | t  | konsonan gandengan |

> ⚠️ **Gantungan ra repa (53)** adalah bentuk vokalik (ra repa/guwung) yang
> mewakili /rə/ → ditransliterasi "re", bukan "r".

---

## 2. Sifat Spasial Glyph (penting untuk input berbasis deteksi)

Satu suku kata ortografis **tidak** menempati satu posisi-x. Posisi relatif
glyph menentukan cara pengelompokan deteksi YOLO:

| Posisi | Glyph |
|--------|-------|
| **Kiri** (pra-aksara) | taling (38) |
| **Kanan** (pasca-aksara) | tedong (35), bisah (42) |
| **Atas** | ulu (36), pepet (39), cecek (40), surang (41) |
| **Bawah** | suku (37), gantungan (18–34, 52–54) |
| **Tengah** | aksara dasar / wianjana |

Konsekuensi penting:

- `ulu`, `suku`, `pepet`, `cecek`, `surang`, `gantungan`, `adeg-adeg`
  bertumpuk **vertikal** dengan aksara dasarnya (≈ posisi-x sama) → dideteksi
  pada **grup** yang sama.
- `taling` (kiri) dan `tedong` (kanan) menempati **posisi-x tersendiri**
  sehingga **terpisah** dari grup aksara dasar. Inilah alasan aturan Kesiman
  memakai konteks `PREV.BASE = TALENG` dan `NEXT.BASE = TEDONG` (lihat §4).

Karena itu mesin memproses dengan dua tahap:

1. **Pengelompokan vertikal** (`group_vertical`): glyph yang berbagi posisi-x
   (dalam ambang `X_GROUP_THRESHOLD`, default 15 px) digabung menjadi satu
   grup → satu kandidat suku kata.
2. **Pemindaian sekuensial kiri→kanan** (`transliterate_line`): `taling`
   dibawa sebagai vokal pra-aksara untuk grup berikutnya, dan `tedong`
   diterapkan mundur ke suku kata sebelumnya (taling + dasar + tedong → "o").

---

## 3. Aturan Transliterasi yang Diterapkan

Aturan diterapkan berurutan untuk tiap grup aksara dasar.

**R1 — Vokal inheren.**
Setiap aksara wianjana berbunyi konsonan + "a" (mis. ID 4 → "ka").

**R2 — Pangangge suara mengganti vokal inheren.**
ulu→i, suku→u, taling→e, pepet→e. `tedong` sendiri = "a" panjang (ā,
ditulis "a"); `taling` + `tedong` = "o".

**R3 — Gantungan/gempelan membentuk gugus konsonan.**
Gantungan mematikan vokal inheren konsonan **sebelumnya**, lalu konsonan
gantungan menjadi anggota gugus. **Vokal nukleus menempel pada konsonan
TERAKHIR dalam gugus.**
Contoh: `ka` + gantungan `ta` → "kta" (bukan "kt"); `ka` + gantungan `ta` +
`ulu` → "kti".

**R4 — Pangangge tengenan menambah koda.**
cecek→-ng, surang→-r, bisah→-h, ditambahkan **setelah** vokal.
Contoh: `ka` + cecek → "kang".

**R5 — Adeg-adeg mematikan vokal.**
Konsonan menjadi mati (tanpa vokal). Contoh: `ka` + adeg-adeg → "k".

**R6 — Aksara suara & aksara vokalik.**
Aksara suara (45–47) = vokal mandiri a/i/u. Aksara vokalik (la lenga 51,
gantungan ra repa 53) sudah membawa vokal "e" sehingga tidak diberi vokal
inheren lagi.

### 3.1 Urutan pemrosesan dalam satu grup

1. Bangun gugus konsonan dari aksara dasar + gantungan (urut atas→bawah).
2. Tentukan vokal nukleus (R1/R2/R5/R6) — menempel pada konsonan terakhir.
3. Tambahkan koda (R4): cecek/surang/bisah.

### 3.2 Penanganan taling & tedong antar-grup

- Grup berisi **taling saja** → set penanda `pending_taling`, diterapkan pada
  grup aksara dasar berikutnya (→ vokal "e").
- Grup berisi **tedong saja** → modifikasi suku kata **sebelumnya**:
  - jika vokalnya berasal dari taling ("e") → menjadi "o";
  - jika vokalnya "a"/kosong → tetap "a" (ā panjang);
  - jika ulu/suku → vokal panjang, romanisasi tetap (i/u).

---

## 4. Aturan Fonologis Kesiman (referensi naskah lontar)

Aturan berikut dirangkum dari Kesiman dkk. (lihat §7) dan menjadi dasar
penanganan taling/tedong yang terpisah secara spasial. Notasi: `CURR` = glyph
sekarang, `PREV`/`NEXT` = tetangga kiri/kanan, `BASE.LEVEL1` = lapis penanda
atas/kiri.

- **RULE1** — Bila aksara dasar bertipe konsonan (CON/GEM) → ambil bunyi awal
  konsonan (mis. "MA" → "M").
- **RULE2** — Bila tidak ada penanda bawah → tambahkan bunyi suku kata dasar
  (vokal inheren) → "MA".
- **RULE3 & RULE4** — Bila `PREV.BASE = TALING` dan `NEXT.BASE = TEDONG` →
  bunyi menjadi vokal "o" (kombinasi taling+tedong). → diimplementasi pada
  `_apply_tedong`/`_determine_vowel`.
- **RULE5 & RULE6** — Varian dengan `PREV2.BASE = TALING` (taling berada dua
  posisi sebelumnya karena ada gugus) untuk bunyi "e"/"o".
- **RULE7** — Bila `NEXT.BASE = NANIA` (gantungan nya/ya) → gabungkan bunyi
  awal glyph berikutnya (pembentukan gugus). → ditangani oleh R3 (gugus
  konsonan).
- **RULE8** — Bila tidak ada penanda atas/bawah, `PREV` bukan taling, dan
  `NEXT` bukan adeg-adeg/gantungan → konsonan memakai vokal inheren "a".

Contoh dari Kesiman: urutan glyph "TA", "MA", "NA" (masing-masing konsonan
dengan vokal inheren) menghasilkan **"TAMANA"** — perilaku ini diverifikasi
pada pengujian mesin (`tamana`).

---

## 5. Perbaikan terhadap Implementasi Sebelumnya

Versi lama `transliteration.py` memiliki beberapa kesalahan yang telah
diperbaiki:

1. **Gantungan menghilangkan vokal.** Dulu `ka` + gantungan `ta` → "kt".
   Seharusnya konsonan gantungan menerima vokal suku kata → **"kta"**.
2. **Vokal menempel pada konsonan yang salah.** ulu/suku dulu menempel pada
   aksara dasar; seharusnya pada konsonan **terakhir** gugus (`kti`, bukan
   `kit`).
3. **Taling/tedong diperlakukan sebagai tumpukan vertikal.** Padahal keduanya
   adalah glyph horizontal (taling=kiri, tedong=kanan) sehingga jarang masuk
   ke grup aksara dasar. Kini diproses sekuensial (look-behind/look-ahead)
   sesuai aturan Kesiman.
4. **Tedong sendiri salah dibaca "o".** Tedong sendiri = "a" panjang (ā);
   hanya **taling + tedong** = "o".
5. **Aksara vokalik salah pemetaan.** `la lenga` (51) = "le" dan
   `gantungan ra repa` (53) = "re", bukan "l"/"r".

---

## 6. Keterbatasan yang Diketahui

- **Vokal pepet vs taling.** Keduanya diromanisasi "e". Beberapa sistem
  membedakan é (taling) dan ě (pepet); di sini disederhanakan menjadi "e".
- **Vokal inheren /ə/ di akhir kata.** Dalam ortografi, "a" inheren dilafalkan
  /ə/ di akhir kata dan pada prefiks ma-, pa-, da-. Karena lontar tidak
  memakai spasi antar-kata, batas kata tidak diketahui sehingga vokal tetap
  ditulis "a".
- **Gugus lintas kata.** Aksara Bali membentuk gugus (gantungan) yang dapat
  melewati batas kata; pemisahan kata yang benar memerlukan kamus dan berada
  di luar lingkup mesin berbasis aturan ini.
- **Akurasi bergantung pada deteksi.** Kesalahan posisi/kelas dari YOLO
  (mis. `X_GROUP_THRESHOLD` yang tidak pas) akan merambat ke hasil
  transliterasi.

---

## 7. Sumber & Referensi (untuk daftar pustaka paper)

Sumber-sumber berikut dapat dipakai sebagai rujukan pada paper Anda. Konten
telah diparafrasa untuk mematuhi batasan lisensi.

**Aturan fonologis & transliterasi naskah lontar (utama):**

1. Kesiman, M. W. A., Burie, J.-C., Ogier, J.-M., et al.
   *Knowledge Representation and Phonological Rules for the Automatic
   Transliteration of Balinese Script on Palm Leaf Manuscript.*
   Computación y Sistemas, Vol. 21, No. 4, 2017.
   <https://www.cys.cic.ipn.mx/ojs/index.php/CyS/article/view/2851>
   (sumber RULE1–RULE8 pada §4).

2. Kesiman, M. W. A., dkk. *Sistem/komponen transliterasi aksara Bali pada
   naskah lontar* (dokumen `2018Kesiman115541.pdf`, koleksi penulis) — bagian
   aturan fonologis berbasis segmentasi glyph.

3. Kesiman, M. W. A., dkk.
   *A Complete Scheme of Spatially Categorized Glyph Recognition for the
   Transliteration of Balinese Palm Leaf Manuscripts.* ICDAR/IEEE, 2017.
   <https://ieeexplore.ieee.org/document/8269960>

**Dataset & model deteksi karakter (yang dipakai proyek ini):**

4. *DeepLontar dataset for handwritten Balinese character detection and
   syllable recognition on Lontar manuscript.* Scientific Data (Nature), 2022.
   <https://www.nature.com/articles/s41597-022-01867-5>
   (sumber 55 kelas karakter pada §1).

**Pendekatan rule-based + Levenshtein (referensi yang Anda miliki):**

5. *Transliteration Balinese Latin Text Becomes Aksara Bali Using Rule Base
   And Levenshtein Distance Approach.* ResearchGate, 2020.
   <https://www.researchgate.net/publication/341341196>

**Ortografi & kaidah Pasang Aksara Bali (standar):**

6. R. Ishida. *Balinese orthography notes* (W3C/r12a) — ringkasan kaidah
   ortografi Bali modern (vowel signs, gantungan/gempelan, adeg-adeg,
   pangangge tengenan). <https://r12a.github.io/scripts/bali/ban>

7. The Unicode Standard, Version 16.0 — Bab 17.3 (Balinese).
   <https://unicode.org/versions/Unicode16.0.0/core-spec/chapter-17/>

8. Library of Congress. *Balinese Romanization Table.*
   <https://www.loc.gov/catdir/cpso/romanization/balinese.pdf>

9. Ida Bagus Adi Sudewa. *The Balinese Alphabet (Babad Bali).*
   <http://www.babadbali.com/aksarabali/alphabet.htm>

10. A. B. Perdana. *Musical Symbols and Sasak Characters in the Balinese
    Script* (Unicode Technical Note 51, 2023).
    <https://www.unicode.org/notes/tn51/UTN51-Balinese-Characters-1.pdf>

> *Konten dari sumber web (terutama no. 6) telah diparafrasa/diringkas untuk
> memenuhi batasan lisensi.*
