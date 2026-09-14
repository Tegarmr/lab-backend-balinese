"""
Rule-based Balinese aksara (script) -> Latin transliteration engine.

This engine converts the YOLO character detections of a single lontar
(palm-leaf) text line into a Latin reading, following the *Pasang Aksara
Bali* (Balinese spelling) conventions and the phonological/positional rules
described for palm-leaf manuscript transliteration.

The full rule set, worked examples and the bibliographic sources are
documented in ``../aturan_transliterasi_aksara_bali.md`` (sejajar dengan
folder ``backend``).

Core abugida behaviour
----------------------
Balinese is an *abugida*: every consonant letter (aksara wianjana) carries an
inherent vowel /a/. That inherent vowel is:

  * replaced by a vowel sign (pangangge suara: ulu, suku, taling, pepet,
    tedong),
  * suppressed by ``adeg-adeg`` (the virama / vowel killer), or
  * suppressed because the consonant is the *first* member of a consonant
    cluster written with a subjoined ``gantungan`` / ``gempelan`` glyph.

Spatial behaviour of the glyphs (critical for detection-based input)
--------------------------------------------------------------------
A single orthographic syllable does **not** occupy a single x-position:

  * ``taling`` (e) is a *pre-base* glyph -> drawn to the **left** of the base.
  * ``tedong``                           -> drawn to the **right** of the base.
  * ``ulu`` (i), ``pepet`` (e), ``cecek`` (ng), ``surang`` (r) -> **above**.
  * ``suku`` (u), ``gantungan`` (subjoined consonant) -> **below**.

Because of this, ``taling`` and ``tedong`` are detected as their *own*
horizontal positions (their own groups), while ``ulu/suku/pepet/cecek/surang/
gantungan/adeg-adeg`` stack vertically with their base (same x). The engine
therefore:

  1. groups vertically-stacked glyphs that share an x-position, then
  2. scans the groups left-to-right, using ``taling`` as a *look-behind*
     marker for the following base and ``tedong`` as a *look-ahead* marker
     that modifies the preceding syllable (taling + base + tedong => "o").
"""

import logging
from dataclasses import dataclass, field

from app.config import X_GROUP_THRESHOLD

logger = logging.getLogger(__name__)


@dataclass
class CharPosition:
    """A detected character with its position and bounding box."""
    class_id: int
    class_name: str
    x: float                    # x_center
    y: float                    # y_center
    confidence: float = 0.0
    det_index: int = -1  # index into the line's detection list (for crop lookup)
    # Bounding box (xyxy) — used for geometry-based glyph association.
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0


@dataclass
class CharGroup:
    """A group of characters at the same x-position (vertically stacked)."""
    x: float
    characters: list[CharPosition] = field(default_factory=list)

    def sort_by_y(self):
        """Sort characters top-to-bottom."""
        self.characters.sort(key=lambda c: c.y)


# ══════════════════════════════════════════════════════════
# Class-ID groupings (must match detection.CLASS_MAP)
# ══════════════════════════════════════════════════════════

# Aksara Wianjana (18 basic consonants) — inherent vowel "a"
WIANJANA_IDS = set(range(0, 18))            # 0-17

# Gantungan / Gempelan (subjoined consonants) — continue a consonant cluster
GANTUNGAN_IDS = set(range(18, 35))          # 18-34

# Pangangge Suara (vowel signs)
TEDONG_ID = 35
ULU_ID = 36
SUKU_ID = 37
TALING_ID = 38
PEPET_ID = 39
PENGANGGE_SUARA_IDS = {TEDONG_ID, ULU_ID, SUKU_ID, TALING_ID, PEPET_ID}

# Pangangge Tengenan (syllable-final consonant marks)
CECEK_ID = 40                               # -ng
SURANG_ID = 41                              # -r
BISAH_ID = 42                               # -h
PENGANGGE_TENGENAN_IDS = {CECEK_ID, SURANG_ID, BISAH_ID}

# Special / structural glyphs
ADEG_ADEG_ID = 43                           # virama (vowel killer)
TITIK_ID = 44                               # carik / punctuation

# Aksara Suara (independent / standalone vowels)
AKSARA_SUARA_IDS = {45, 46, 47}             # A-kara, I-kara, U-kara

# Aksara Wayah / Sualalita (consonants for Sanskrit-Kawi loanwords)
SA_SAGA_ID = 48
NA_RAMBAT_ID = 49
DA_MADU_ID = 50
LA_LENGA_ID = 51                            # NOTE: a *vocalic* -> "le" (lě)
AKSARA_WAYAH_IDS = {SA_SAGA_ID, NA_RAMBAT_ID, DA_MADU_ID, LA_LENGA_ID}

# Gantungan Wayah (subjoined loanword consonants)
GANT_DA_MADU_ID = 52
GANT_RA_REPA_ID = 53                        # NOTE: a *vocalic* -> "re" (rě)
GANT_TA_TAWA_ID = 54
GANTUNGAN_WAYAH_IDS = {GANT_DA_MADU_ID, GANT_RA_REPA_ID, GANT_TA_TAWA_ID}


# ══════════════════════════════════════════════════════════
# Sound mappings (romanisation)
# ══════════════════════════════════════════════════════════

# Base consonant letters (Aksara Wianjana) — the bare consonant; the inherent
# "a" is supplied by the vowel logic, not stored here.
WIANJANA_CONSONANT = {
    0: "h", 1: "n", 2: "c", 3: "r", 4: "k",
    5: "d", 6: "t", 7: "s", 8: "w", 9: "l",
    10: "m", 11: "g", 12: "b", 13: "ng", 14: "p",
    15: "j", 16: "y", 17: "ny",
}

# Gantungan / Gempelan -> the consonant it contributes to the cluster.
GANTUNGAN_CONSONANT = {
    18: "h", 19: "n", 20: "c", 21: "r", 22: "d",
    23: "t", 24: "s", 25: "w", 26: "l", 27: "m",
    28: "g", 29: "b", 30: "ng", 31: "p", 32: "j",
    33: "y", 34: "ny",
}

# Aksara Wayah / Sualalita base consonants.
WAYAH_CONSONANT = {
    SA_SAGA_ID: "s",    # sa saga  (ś)
    NA_RAMBAT_ID: "n",  # na rambat (ṇ)
    DA_MADU_ID: "d",    # da madu  (dh), e.g. "Dharma"
    # LA_LENGA_ID handled as a vocalic ("le"), see _build_syllable.
}

# Gantungan Wayah -> the consonant it contributes (non-vocalic ones).
GANTUNGAN_WAYAH_CONSONANT = {
    GANT_DA_MADU_ID: "d",   # gantungan da madu
    GANT_TA_TAWA_ID: "t",   # gantungan ta tawa
    # GANT_RA_REPA_ID handled as a vocalic ("re"), see _build_syllable.
}

# Pangangge Tengenan (finals) -> coda sound.
TENGENAN_SOUND = {
    CECEK_ID: "ng",   # cecek
    SURANG_ID: "r",   # surang
    BISAH_ID: "h",    # bisah
}

# Aksara Suara (standalone vowels).
SUARA_SOUND = {45: "a", 46: "i", 47: "u"}


def _consonant_of(class_id: int) -> str | None:
    """Consonant letter for a base/wayah consonant id (None if not one)."""
    if class_id in WIANJANA_CONSONANT:
        return WIANJANA_CONSONANT[class_id]
    if class_id in WAYAH_CONSONANT:
        return WAYAH_CONSONANT[class_id]
    return None


def _is_base_consonant(class_id: int) -> bool:
    """True for Aksara Wianjana or non-vocalic Aksara Wayah."""
    return class_id in WIANJANA_IDS or class_id in WAYAH_CONSONANT


def _is_gantungan(class_id: int) -> bool:
    return class_id in GANTUNGAN_IDS or class_id in GANTUNGAN_WAYAH_IDS


def _gantungan_sound(class_id: int) -> str:
    """Romanised contribution of a gantungan (for leftover/visibility notes)."""
    if class_id == GANT_RA_REPA_ID:
        return "re"      # vocalic (rě)
    if class_id in GANTUNGAN_WAYAH_CONSONANT:
        return GANTUNGAN_WAYAH_CONSONANT[class_id]
    return GANTUNGAN_CONSONANT.get(class_id, "")


@dataclass
class _Syllable:
    """Intermediate, mutable representation of one rendered syllable."""
    consonants: str = ""      # consonant cluster, e.g. "kt"
    vowel: str = "a"          # nucleus vowel ("" if killed)
    coda: str = ""            # final consonant(s): ng / r / h
    from_taling: bool = False  # vowel came from taling (needed for tedong->o)
    raw: str | None = None     # punctuation/raw passthrough (overrides render)
    # Provenance (for the "which glyphs form which syllable" breakdown):
    sources: list = field(default_factory=list)  # list[CharPosition]
    rules: list = field(default_factory=list)     # list[str] rule explanations

    def render(self) -> str:
        if self.raw is not None:
            return self.raw
        return f"{self.consonants}{self.vowel}{self.coda}"

    def rule_text(self) -> str:
        return "; ".join(self.rules)


class TransliterationEngine:
    """Rule-based Balinese aksara -> Latin transliteration engine."""

    def __init__(self, x_threshold: int = X_GROUP_THRESHOLD):
        self.x_threshold = x_threshold

    # ──────────────────────────────────────────────────────
    # Vertical grouping (glyphs sharing an x-position)
    # ──────────────────────────────────────────────────────
    def group_vertical(self, detections: list[dict]) -> list[CharGroup]:
        """
        Associate every modifier glyph with the correct base consonant using
        bounding-box geometry, then return one :class:`CharGroup` per
        orthographic syllable (a base plus its stacked / pre / post marks).

        Spatial roles (see ``aturan_transliterasi_aksara_bali.md`` §2):

          * base                : wianjana / wayah / la lenga / aksara suara
          * left  (pra-aksara)  : taling  → attaches to the base on its RIGHT
          * right (pasca-aksara): tedong, bisah → attaches to the base on LEFT
          * above / below       : ulu, suku, pepet, cecek, surang, adeg-adeg,
                                  gantungan → base with the largest horizontal
                                  bounding-box overlap (gantungan biased to the
                                  preceding consonant)

        ``titik`` (punctuation) and any modifier that cannot find a base are
        returned as their own groups, so no detection is ever silently dropped.
        """
        if not detections:
            return []

        positions = [self._to_pos(d, i) for i, d in enumerate(detections)]
        positions.sort(key=lambda p: p.x)

        bases = [p for p in positions if self._is_base_glyph(p.class_id)]

        # One slot per base (keyed by identity), anchored at the base's x.
        slots: dict[int, CharGroup] = {
            id(b): CharGroup(x=b.x, characters=[b]) for b in bases
        }
        extra: list[tuple[float, CharGroup]] = []  # punctuation + orphans

        for p in positions:
            cid = p.class_id
            if self._is_base_glyph(cid):
                continue
            if cid == TITIK_ID:
                extra.append((p.x, CharGroup(x=p.x, characters=[p])))
                continue

            target = self._pick_base(p, bases)
            if target is None:
                # No base on this line → keep visible as its own group.
                extra.append((p.x, CharGroup(x=p.x, characters=[p])))
            else:
                slots[id(target)].characters.append(p)

        ordered = [(b.x, slots[id(b)]) for b in bases] + extra
        ordered.sort(key=lambda t: t[0])
        groups = [g for _, g in ordered]
        for g in groups:
            g.sort_by_y()
        return groups

    @staticmethod
    def _is_base_glyph(class_id: int) -> bool:
        """True for glyphs that anchor a syllable (a consonant or a vowel)."""
        return (
            _is_base_consonant(class_id)
            or class_id == LA_LENGA_ID
            or class_id in AKSARA_SUARA_IDS
        )

    @staticmethod
    def _pick_base(
        p: CharPosition, bases: list[CharPosition]
    ) -> CharPosition | None:
        """
        Choose the base consonant a modifier glyph belongs to, using its
        spatial role and bounding-box geometry.
        """
        if not bases:
            return None

        cid = p.class_id

        # Pre-base taling → nearest base to the RIGHT.
        if cid == TALING_ID:
            right = [b for b in bases if b.x >= p.x]
            if right:
                return min(right, key=lambda b: b.x - p.x)
            return min(bases, key=lambda b: abs(b.x - p.x))

        # Post-base tedong / bisah → nearest base to the LEFT.
        if cid in (TEDONG_ID, BISAH_ID):
            left = [b for b in bases if b.x <= p.x]
            if left:
                return min(left, key=lambda b: p.x - b.x)
            return min(bases, key=lambda b: abs(b.x - p.x))

        # Gantungan subjoins to the PRECEDING consonant: prefer an overlapping
        # base at or to the left of the glyph.
        if _is_gantungan(cid):
            left_overlap = [
                b
                for b in bases
                if (min(p.x2, b.x2) - max(p.x1, b.x1)) > 0 and b.x <= p.x2
            ]
            if left_overlap:
                return max(left_overlap, key=lambda b: b.x)

        # Above / below stacking marks → base with the largest horizontal
        # bounding-box overlap (as a fraction of the modifier's own width).
        width = max(1.0, p.x2 - p.x1)
        best, best_score = None, 0.0
        for b in bases:
            overlap = min(p.x2, b.x2) - max(p.x1, b.x1)
            frac = overlap / width
            if frac > best_score:
                best, best_score = b, frac
        if best is not None and best_score > 0.0:
            return best

        # No horizontal overlap → nearest base by center distance.
        return min(bases, key=lambda b: abs(b.x - p.x))

    @staticmethod
    def _to_pos(det: dict, det_index: int = -1) -> CharPosition:
        xc = det["x_center"]
        yc = det["y_center"]
        w = det.get("width", 0.0)
        h = det.get("height", 0.0)
        # Prefer explicit box corners; fall back to center±half-size.
        x1 = det.get("x1", xc - w / 2)
        y1 = det.get("y1", yc - h / 2)
        x2 = det.get("x2", xc + w / 2)
        y2 = det.get("y2", yc + h / 2)
        return CharPosition(
            class_id=det["class_id"],
            class_name=det["class_name"],
            x=xc,
            y=yc,
            confidence=det.get("confidence", 0.0),
            det_index=det_index,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
        )

    def format_grouped_text(self, groups: list[CharGroup]) -> str:
        """
        Format groups into the display format with parentheses for verticals.

        Example: "(3,2,1) 4 3 9 2 8 9 (2,1,3)"
        """
        parts = []
        for group in groups:
            ids = [str(c.class_id) for c in group.characters]
            if len(ids) > 1:
                parts.append(f"({','.join(ids)})")
            else:
                parts.append(ids[0])
        return " ".join(parts)

    # ──────────────────────────────────────────────────────
    # Line transliteration (sequential, left-to-right)
    # ──────────────────────────────────────────────────────
    def transliterate_line(self, detections: list[dict]) -> str:
        """
        Transliterate one line of detected characters to Latin.

        The groups are scanned left-to-right. ``taling`` is carried forward as
        a pending pre-base vowel for the next base; ``tedong`` is applied
        backwards to the previous syllable (taling+base+tedong => "o").
        """
        syllables = self._line_to_syllables(detections)
        return "".join(s.render() for s in syllables)

    def transliterate_line_detailed(self, detections: list[dict]) -> list[dict]:
        """
        Same as :meth:`transliterate_line` but returns a structured breakdown
        of every rendered syllable so the caller can see *which detected
        glyphs combine into which syllable* and *why* (the rule applied).

        Returns a list of dicts, one per rendered unit::

            {
                "text": "ko",                     # rendered syllable / token
                "rule": "Taling + tedong -> ...", # human-readable explanation
                "glyphs": [                       # contributing detections
                    {"class_id": 38, "class_name": "taling",
                     "det_index": 0, "x": 12.0, "y": 40.0},
                    ...
                ],
            }
        """
        syllables = self._line_to_syllables(detections)
        units: list[dict] = []
        for syl in syllables:
            text = syl.render()
            # Order source glyphs left-to-right, then top-to-bottom for clarity.
            glyphs = sorted(syl.sources, key=lambda c: (round(c.x, 1), c.y))
            units.append(
                {
                    "text": text,
                    "rule": syl.rule_text(),
                    "glyphs": [
                        {
                            "class_id": g.class_id,
                            "class_name": g.class_name,
                            "det_index": g.det_index,
                            "x": g.x,
                            "y": g.y,
                        }
                        for g in glyphs
                    ],
                }
            )
        return units

    def _line_to_syllables(self, detections: list[dict]) -> list["_Syllable"]:
        """
        Build the syllable list from geometry-associated groups.

        Because :meth:`group_vertical` now attaches ``taling``/``tedong`` (and
        every other mark) directly to their base, this is a plain left-to-right
        pass — no look-behind/look-ahead state is required. Each
        :class:`_Syllable` carries its source glyphs (``sources``) and rule
        explanations (``rules``) so the result can be audited glyph-by-glyph.
        """
        groups = self.group_vertical(detections)
        if not groups:
            return []

        syllables: list[_Syllable] = []
        for group in groups:
            cls = self._classify(group)
            members = list(group.characters)

            # Punctuation / separator (titik / carik).
            if cls["titik"]:
                syllables.append(
                    _Syllable(
                        raw=", ",
                        sources=members,
                        rules=["Tanda baca (carik/titik) → pemisah kata (R7)."],
                    )
                )
                continue

            # Normal base consonant with its stacked / pre / post marks.
            if cls["base"] is not None:
                syl = self._build_syllable(cls)
                syl.sources = members
                syllables.append(syl)
                continue

            # Standalone vowel or leftover marks (kept visible, never dropped).
            orphan = self._build_orphan(cls)
            if orphan is not None:
                orphan.sources = members
                syllables.append(orphan)

        return syllables

    # ──────────────────────────────────────────────────────
    # Group classification
    # ──────────────────────────────────────────────────────
    @staticmethod
    def _classify(group: CharGroup) -> dict:
        """Split a group's glyphs into structural roles."""
        info = {
            "base": None,          # CharPosition of base consonant
            "standalone": None,    # CharPosition of aksara suara
            "gantungan": [],       # list[CharPosition] (top-to-bottom order)
            "vowel_signs": [],     # ulu / suku / pepet class ids
            "finals": [],          # cecek / surang / bisah class ids
            "taling": False,
            "tedong": False,
            "adeg": False,
            "titik": False,
        }
        for c in group.characters:
            cid = c.class_id
            if _is_base_consonant(cid) or cid == LA_LENGA_ID:
                info["base"] = c
            elif cid in AKSARA_SUARA_IDS:
                info["standalone"] = c
            elif _is_gantungan(cid):
                info["gantungan"].append(c)
            elif cid == TALING_ID:
                info["taling"] = True
            elif cid == TEDONG_ID:
                info["tedong"] = True
            elif cid in (ULU_ID, SUKU_ID, PEPET_ID):
                info["vowel_signs"].append(cid)
            elif cid in PENGANGGE_TENGENAN_IDS:
                info["finals"].append(cid)
            elif cid == ADEG_ADEG_ID:
                info["adeg"] = True
            elif cid == TITIK_ID:
                info["titik"] = True
        return info

    # ──────────────────────────────────────────────────────
    # Syllable construction
    # ──────────────────────────────────────────────────────
    def _build_syllable(self, cls: dict) -> _Syllable:
        """
        Build a syllable from a base group.

        Rule order:
          R1  Base consonant carries inherent "a".
          R3  Each gantungan extends the consonant cluster and kills the
              inherent vowel of the *preceding* consonant; the nucleus vowel
              attaches to the LAST consonant of the cluster.
          R2  A vowel sign (ulu/suku/taling/pepet, or pending taling) replaces
              the inherent "a" of that last consonant.
          R5  adeg-adeg kills the vowel entirely.
          R4  Pangangge tengenan (cecek/surang/bisah) add the coda.
          R6  Vocalic glyphs (la lenga, gantungan ra repa) already include
              their own "e" vowel.
        """
        syl = _Syllable()
        vowel_override: str | None = None
        rules: list[str] = []

        # ── Build the consonant cluster ──────────────────
        base = cls["base"]
        if base is not None and base.class_id == LA_LENGA_ID:
            # la lenga is a vocalic letter: l + ě
            syl.consonants = "l"
            vowel_override = "e"
            rules.append("Aksara wayah 'la lenga' bersifat vokalik → 'le' (lě) (R6).")
        else:
            cons = _consonant_of(base.class_id) if base is not None else None
            syl.consonants = cons or ""
            if base is not None:
                rules.append(
                    f"Aksara dasar '{base.class_name}' → konsonan '{cons}' "
                    f"dengan vokal inheren /a/ (R1)."
                )

        for g in cls["gantungan"]:
            gid = g.class_id
            if gid == GANT_RA_REPA_ID:
                # vocalic: adds "r" + ě
                syl.consonants += "r"
                vowel_override = "e"
                rules.append(
                    f"'{g.class_name}' bersifat vokalik → menambah 're' (rě) (R6)."
                )
            elif gid in GANTUNGAN_WAYAH_CONSONANT:
                syl.consonants += GANTUNGAN_WAYAH_CONSONANT[gid]
                rules.append(
                    f"'{g.class_name}' (gantungan) menggabung konsonan "
                    f"'{GANTUNGAN_WAYAH_CONSONANT[gid]}' & mematikan /a/ sebelumnya (R3)."
                )
            elif gid in GANTUNGAN_CONSONANT:
                syl.consonants += GANTUNGAN_CONSONANT[gid]
                rules.append(
                    f"'{g.class_name}' (gantungan) menggabung konsonan "
                    f"'{GANTUNGAN_CONSONANT[gid]}' & mematikan /a/ sebelumnya (R3)."
                )

        if not syl.consonants:
            # Nothing usable; emit empty syllable.
            return _Syllable(raw="")

        # ── Determine the nucleus vowel ──────────────────
        syl.vowel, syl.from_taling = self._determine_vowel(cls, vowel_override)
        rules.extend(self._vowel_rule_notes(cls, vowel_override))

        # ── Coda (pangangge tengenan) ────────────────────
        # Deterministic order: ng, r, h.
        for fid in sorted(cls["finals"]):
            syl.coda += TENGENAN_SOUND[fid]
            name = {CECEK_ID: "cecek", SURANG_ID: "surang", BISAH_ID: "bisah"}[fid]
            rules.append(
                f"Pangangge tengenan '{name}' → koda '{TENGENAN_SOUND[fid]}' (R4)."
            )

        syl.rules = rules
        return syl

    @staticmethod
    def _vowel_rule_notes(cls: dict, vowel_override: str | None) -> list[str]:
        """Human-readable notes explaining the nucleus-vowel decision."""
        notes: list[str] = []
        taling = cls["taling"]
        tedong = cls["tedong"]

        if cls["adeg"] and vowel_override is None:
            notes.append("Adeg-adeg mematikan vokal (konsonan mati) (R5).")
            return notes
        if vowel_override is not None:
            return notes  # already explained by the vocalic glyph note
        if taling and tedong:
            notes.append("Taling (kiri) + tedong (kanan) → vokal 'o' (R2).")
            return notes
        if taling:
            notes.append("Taling (pra-aksara, kiri) → vokal 'e' (R2).")
            return notes
        if tedong:
            notes.append(
                "Tedong (pasca-aksara, kanan) → vokal panjang 'a' (ā) (R2)."
            )
            return notes
        for vid in cls["vowel_signs"]:
            if vid == ULU_ID:
                notes.append("Pangangge suara 'ulu' → vokal 'i' (R2).")
            elif vid == SUKU_ID:
                notes.append("Pangangge suara 'suku' → vokal 'u' (R2).")
            elif vid == PEPET_ID:
                notes.append("Pangangge suara 'pepet' → vokal 'e' (ě) (R2).")
        return notes

    @staticmethod
    def _determine_vowel(
        cls: dict, vowel_override: str | None
    ) -> tuple[str, bool]:
        """
        Resolve the nucleus vowel and whether it originated from taling.

        Returns (vowel, from_taling).
        """
        taling = cls["taling"]
        tedong = cls["tedong"]

        # adeg-adeg suppresses the vowel (unless a vocalic forced one).
        if cls["adeg"] and vowel_override is None:
            return "", False

        # Vocalic glyph supplies its own vowel.
        if vowel_override is not None:
            return vowel_override, False

        # taling + tedong in the same group => "o".
        if taling and tedong:
            return "o", True
        if taling:
            return "e", True
        if tedong:
            # tedong alone = long "a" (ā), romanised "a".
            return "a", False

        # ulu / suku / pepet (only one expected).
        for vid in cls["vowel_signs"]:
            if vid == ULU_ID:
                return "i", False
            if vid == SUKU_ID:
                return "u", False
            if vid == PEPET_ID:
                return "e", False

        # Inherent vowel.
        return "a", False

    def _build_orphan(self, cls: dict) -> _Syllable | None:
        """
        Handle a group that has no base consonant.

        With geometry-based association almost every mark lands on a base, so
        orphans only happen when a whole line has no base at all. To honour the
        "never drop a detection" rule, every leftover glyph still produces a
        *visible* unit:

          * standalone vowel (aksara suara) → its own vowel;
          * stray finals (cecek/surang/bisah) → emitted as their coda sound;
          * stray gantungan / pangangge suara / adeg-adeg → an empty-text unit
            carrying an explanatory note (so it shows up in the breakdown
            without corrupting the Latin reading).
        """
        # ── Standalone independent vowel (aksara suara) ──
        if cls["standalone"] is not None:
            syl = _Syllable(consonants="", vowel="")
            syl.vowel = SUARA_SOUND[cls["standalone"].class_id]
            syl.rules.append(
                f"Aksara suara '{cls['standalone'].class_name}' "
                f"→ vokal mandiri '{syl.vowel}'."
            )
            for fid in sorted(cls["finals"]):
                syl.coda += TENGENAN_SOUND[fid]
                name = {CECEK_ID: "cecek", SURANG_ID: "surang", BISAH_ID: "bisah"}[fid]
                syl.rules.append(
                    f"Pangangge tengenan '{name}' → koda '{TENGENAN_SOUND[fid]}' (R4)."
                )
            return syl

        # ── Stray finals only → emit their coda ──
        coda = "".join(TENGENAN_SOUND[fid] for fid in sorted(cls["finals"]))
        if coda:
            syl = _Syllable(consonants="", vowel="", coda=coda)
            syl.rules.append(f"Pangangge tengenan lepas → koda '{coda}' (R4).")
            return syl

        # ── Stray gantungan / vowel-signs / taling / tedong / adeg ──
        # Keep them VISIBLE (empty render) instead of silently discarding.
        notes: list[str] = []
        for g in cls["gantungan"]:
            snd = _gantungan_sound(g.class_id)
            notes.append(
                f"Gantungan lepas '{g.class_name}'"
                + (f" ('{snd}')" if snd else "")
                + " — tanpa aksara dasar, tidak digabung."
            )
        for vid in cls["vowel_signs"]:
            vname = {ULU_ID: "ulu", SUKU_ID: "suku", PEPET_ID: "pepet"}[vid]
            notes.append(
                f"Pangangge suara '{vname}' lepas — tanpa aksara dasar."
            )
        if cls["taling"]:
            notes.append("Taling lepas — tanpa aksara dasar di sebelah kanan.")
        if cls["tedong"]:
            notes.append("Tedong lepas — tanpa aksara dasar di sebelah kiri.")
        if cls["adeg"]:
            notes.append("Adeg-adeg lepas — tanpa aksara dasar.")
        if notes:
            return _Syllable(raw="", rules=notes)

        return None

    # ──────────────────────────────────────────────────────
    # Whole-document helper (API used by the router)
    # ──────────────────────────────────────────────────────
    def transliterate_all_lines(
        self, all_detections: list[list[dict]]
    ) -> tuple[list[str], list[str], list[list[dict]], list[list[dict]]]:
        """
        Transliterate all lines.

        Returns (transliterations, grouped_texts, positions_per_line,
        syllables_per_line), where ``syllables_per_line[i]`` is the structured
        syllable breakdown produced by :meth:`transliterate_line_detailed`.
        """
        transliterations = []
        grouped_texts = []
        positions_per_line = []
        syllables_per_line = []

        for line_dets in all_detections:
            groups = self.group_vertical(line_dets)
            grouped_texts.append(self.format_grouped_text(groups))

            positions_per_line.append([
                {
                    "class_id": d["class_id"],
                    "class_name": d["class_name"],
                    "x": d["x_center"],
                    "y": d["y_center"],
                }
                for d in line_dets
            ])

            transliterations.append(self.transliterate_line(line_dets))
            syllables_per_line.append(self.transliterate_line_detailed(line_dets))

        return (
            transliterations,
            grouped_texts,
            positions_per_line,
            syllables_per_line,
        )
