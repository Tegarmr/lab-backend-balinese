Angka dari YOLO itu adalah `class_id`, dan pemetaannya ada di `CLASS_MAP` pada `backend/app/services/detection.py`. Penting: indeksnya **mulai dari 0**, jadi `0 = ha`, bukan `1 = ha`. Ada 55 kelas total.

Berikut daftar lengkapnya, dikelompokkan sesuai fungsinya:

## Aksara Wianjana — 18 konsonan dasar (vokal inheren "a")
| ID | Aksara | Bunyi | ID | Aksara | Bunyi |
|----|--------|-------|----|--------|-------|
| 0 | ha | h | 9 | la | l |
| 1 | na | n | 10 | ma | m |
| 2 | ca | c | 11 | ga | g |
| 3 | ra | r | 12 | ba | b |
| 4 | ka | k | 13 | nga | ng |
| 5 | da | d | 14 | pa | p |
| 6 | ta | t | 15 | ja | j |
| 7 | sa | s | 16 | ya | y |
| 8 | wa | w | 17 | nya | ny |

## Gantungan / Gempelan — konsonan gandengan (ID 18–34)
| ID | Nama | ID | Nama |
|----|------|----|------|
| 18 | Gantungan ha | 27 | Gantungan ma |
| 19 | Gantungan na | 28 | Gantungan ga |
| 20 | Gantungan ca | 29 | Gantungan ba |
| 21 | Gantungan ra | 30 | Gantungan nga |
| 22 | Gantungan da | 31 | Gantungan pa |
| 23 | Gantungan ta | 32 | Gantungan ja |
| 24 | Gantungan sa | 33 | Gantungan ya |
| 25 | Gantungan wa | 34 | Gantungan nya |
| 26 | Gantungan la | | |

## Pangangge Suara — penanda vokal (ID 35–39)
| ID | Nama | Fungsi |
|----|------|--------|
| 35 | Tedong | "a" panjang (ā); taling+tedong → "o" |
| 36 | ulu | vokal "i" |
| 37 | suku | vokal "u" |
| 38 | taling | vokal "e" |
| 39 | pepet | vokal "e" (ě) |

## Pangangge Tengenan — konsonan akhir/koda (ID 40–42)
| ID | Nama | Koda |
|----|------|------|
| 40 | cecek | -ng |
| 41 | surang | -r |
| 42 | bisah | -h |

## Glyph struktural (ID 43–44)
| ID | Nama | Fungsi |
|----|------|--------|
| 43 | adeg-adeg | virama — mematikan vokal |
| 44 | titik | tanda baca / pemisah |

## Aksara Suara — vokal mandiri (ID 45–47)
| ID | Nama | Bunyi |
|----|------|-------|
| 45 | A kara | a |
| 46 | I kara | i |
| 47 | U kara | u |

## Aksara Wayah / Sualalita — untuk serapan Sanskerta-Kawi (ID 48–51)
| ID | Nama | Bunyi |
|----|------|-------|
| 48 | sa saga | s (ś) |
| 49 | na rambat | n (ṇ) |
| 50 | da madu | d (dh) |
| 51 | la lenga | **le** (vokalik lě) |

## Gantungan Wayah (ID 52–54)
| ID | Nama | Bunyi |
|----|------|-------|
| 52 | Gantungan da madu | d |
| 53 | Gantungan ra repa | **re** (vokalik rě) |
| 54 | Gantungan ta tawa | t |

Dua catatan yang gampang bikin salah baca: **la lenga (51)** dan **gantungan ra repa (53)** itu vokalik — sudah membawa vokal "e" sendiri, jadi ditransliterasi "le"/"re", bukan "l"/"r". Daftar `class_id` ini harus selalu sama persis antara `detection.py` (`CLASS_MAP`) dan pengelompokan di `transliteration.py`, karena mesin memetakan lewat angka, bukan nama.