#!/usr/bin/env python3
"""Build mss_timing.json — exact per-verse cues for the M. S. Subbulakshmi recording.

Boundaries come from breath-gap detection (ffmpeg silencedetect) plus
whisper word-timestamp anchors, computed against the 29:41 recording
(duration 1780.99 s). Stotram śloka boundaries are aligned with dynamic
programming over the detected gaps, which fall on half-line breaths.

Inputs:
  /tmp/silences_fine.txt  (ffmpeg silencedetect noise=-27dB d=0.18) — preamble/phala snapping
  /tmp/silences_24.txt    (ffmpeg silencedetect noise=-24dB d=0.12) — stotram breaths
  /tmp/transcript_words.txt (faster-whisper word timestamps) — anchors
Run only when re-deriving cues; the JSON output is committed.
"""

import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent / "source" / "mss_timing.json"

def load_gaps(path="/tmp/silences_fine.txt", min_dur=0.0):
    gaps = []
    start = None
    for line in open(path):
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m:
            start = float(m.group(1))
            continue
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and start is not None:
            if float(m.group(1)) - start >= min_dur:
                gaps.append((start, float(m.group(1))))
            start = None
    merged = []
    for s, e in gaps:
        if merged and s - merged[-1][1] < 0.6:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged

GAPS = load_gaps()
# True breaths (~0.5 s of tanpura between phrases); intra-phrase dips are shorter.
BREATHS = load_gaps("/tmp/silences_24.txt", min_dur=0.28)

def snap(t, tol=0.7):
    """Snap an estimated boundary to the nearest gap; return (sing_end, next_start)."""
    best = None
    for s, e in GAPS:
        mid = (s + e) / 2
        if abs(mid - t) < tol and (best is None or abs(mid - t) < abs((best[0] + best[1]) / 2 - t)):
            best = (s, e)
    return best

def load_anchors():
    """Fuzzy-match whisper transcript phrases to śloka IAST; return {śloka_n: start_time}."""
    import unicodedata
    from rapidfuzz import fuzz

    data_js = (Path(__file__).resolve().parents[1] / "data" / "stotram.js").read_text()
    data = json.loads(data_js.replace("window.STOTRAM = ", "", 1).rstrip(";\n"))
    sto = [v for v in data["learn"] if v["section"] == "stotram"]

    def norm(s):
        s = unicodedata.normalize("NFD", s.lower())
        s = "".join(c for c in s if not unicodedata.combining(c))
        return re.sub(r"[^a-z]", "", s)

    prefixes = [norm(v["iast"])[:44] for v in sto]
    words = []
    for line in open("/tmp/transcript_words.txt"):
        parts = line.split(None, 2)
        if len(parts) == 3:
            words.append((float(parts[0]), parts[2].strip()))
    words = [(a, w) for a, w in words if 400 < a < 1360]

    hits = {}  # śloka -> (start_time, score)
    # Pass 1: windows that begin right after a breath (strongest signal).
    gap_ends = [e for s, e in BREATHS if 400 < e < 1360]
    for g in gap_ends:
        win = [w for w in words if g - 0.25 <= w[0] < g + 3.2][:8]
        if len(win) < 4:
            continue
        q = norm("".join(w for _, w in win))[:44]
        if len(q) < 22:
            continue
        scores = sorted(
            ((fuzz.ratio(q, p), k) for k, p in enumerate(prefixes)), reverse=True
        )
        (s1, k1), (s2, _) = scores[0], scores[1]
        if s1 >= 72 and s1 - s2 >= 10:
            n = k1 + 1
            if n not in hits or s1 > hits[n][1]:
                hits[n] = (g, s1)
    # Pass 2: sliding windows anywhere, for boundaries whose breath is elided
    # or was missed. Stricter thresholds since window starts are noisier.
    for i in range(len(words)):
        win = words[i : i + 8]
        if len(win) < 5:
            continue
        q = norm("".join(w for _, w in win))[:44]
        if len(q) < 26:
            continue
        scores = sorted(
            ((fuzz.ratio(q, p), k) for k, p in enumerate(prefixes)), reverse=True
        )
        (s1, k1), (s2, _) = scores[0], scores[1]
        if s1 >= 80 and s1 - s2 >= 14:
            n = k1 + 1
            if n not in hits or s1 > hits[n][1] + 4:
                hits[n] = (win[0][0], s1)
    return {n: t for n, (t, _) in hits.items()}

def stotram_bounds():
    """Deterministic breath-counting alignment, cross-checked by transcript anchors.

    Between śloka 1's start (403.05, after the long pause) and śloka 107's
    start (1352.90) there are exactly 211 sung segments separated by breaths.
    Śloka 1 takes 3 segments (sung slowly, with an extra pause), ślokas 14 and
    53 are sung compressed in a single breath, every other śloka takes exactly
    2 segments (one per half-line). Śloka 107 ends with its "oṃ nama iti" tail
    at 1364.71; vanamālī (108) is sung three times from 1366.15 to 1395.27.
    All of this was verified word-by-word with whisper (small + large-v3).
    """
    A = 403.05
    core = [(s, e) for s, e in BREATHS if A < s < 1353.0]
    if len(core) != 211:
        raise SystemExit(f"expected 211 breaths in the stotram, got {len(core)}")

    seg_counts = {1: 3, 14: 1, 53: 1}
    bounds = []
    start = A
    idx = 0
    for k in range(1, 107):
        idx += seg_counts.get(k, 2)
        sil_start, sil_end = core[idx - 1]
        bounds.append((start, sil_start))
        start = sil_end
    assert abs(start - 1352.90) < 0.05, start
    bounds.append((1352.90, 1364.71))   # śloka 107 + sarvapraharaṇāyudha oṃ nama iti
    bounds.append((1366.15, 1395.27))   # vanamālī, sung three times

    # transcript-verified śloka starts (whisper small/large-v3, both sessions)
    checks = {
        2: 415.85, 10: 489.55, 15: 529.51, 16: 539.22, 23: 602.69, 24: 611.67,
        47: 820.40, 49: 839.37, 54: 878.15, 55: 887.12, 71: 1032.90,
        87: 1177.00, 89: 1194.49, 96: 1254.64, 100: 1289.5, 102: 1307.4,
    }
    # Whisper word timestamps drift up to ~1 s; the checks exist to catch
    # half-line (~4.3 s) parity slips, so 1.2 s tolerance is plenty tight.
    for n, t in checks.items():
        got = bounds[n - 1][0]
        if abs(got - t) > 1.2:
            raise SystemExit(f"anchor check failed for śloka {n}: {got} vs {t}")
    return [(round(a, 2), round(b, 2)) for a, b in bounds]

def s(t, tol=0.7):
    """Snapped start: singing resumes at gap end."""
    g = snap(t, tol)
    return round(g[1], 2) if g else round(t, 2)

def e(t, tol=0.7):
    """Snapped end: singing stops at gap start."""
    g = snap(t, tol)
    return round(g[0], 2) if g else round(t, 2)

cues = {}

# Opening — whisper anchors + gap snapping
cues["opening"] = [
    (1.94, 14.02),
    (14.56, 23.41),
    (23.89, 32.87),
    (33.31, 41.75),
    (42.23, 55.12),  # yasya smaraṇa… + oṃ namo viṣṇave prabhaviṣṇave
]

# Pūrva pīṭhikā dialogue (uvāca lines folded into the following verse)
cues["purva"] = [
    (55.12, 67.42),    # vaiśampāyana uvāca + śrutvā dharmān
    (67.73, 79.79),    # yudhiṣṭhira uvāca + kimekaṃ daivataṃ
    (80.14, 89.33),    # ko dharmaḥ
    (89.80, 100.18),   # bhīṣma uvāca + jagatprabhuṃ
    (100.63, 109.40),  # tameva cārcayan
    (109.67, 118.96),  # anādinidhanaṃ
    (119.48, e(128.6, 1.0)),   # brahmaṇyaṃ
    (s(128.6, 1.0), e(138.1, 1.0)),  # eṣa me
    (s(138.1, 1.0), 146.85),   # paramaṃ yo
    (147.40, 156.85),  # pavitrāṇāṃ
    (157.25, 165.73),  # yataḥ sarvāṇi
    (166.17, 175.19),  # tasya lokapradhānasya
    (175.41, 184.23),  # yāni nāmāni
    (184.52, 194.00),  # ṛṣirnāmnāṃ
    (194.21, 203.03),  # amṛtāṃśūdbhavo
    (203.55, 212.50),  # viṣṇuṃ jiṣṇuṃ
    (213.12, 265.89),  # nyāsa (asya śrīviṣṇor… viniyogaḥ)
]

# Dhyānam ("dhyānam" announcement folded into kṣīrodanvat)
cues["dhyana"] = [
    (266.68, 292.25),  # kṣīrodanvat
    (292.70, 315.63),  # bhūḥ pādau
    (316.13, 319.64),  # oṃ namo bhagavate vāsudevāya
    (320.29, 339.35),  # śāntākāraṃ
    (339.98, 353.72),  # meghaśyāmaṃ
    (354.30, 362.82),  # namaḥ samastabhūtānām
    (363.34, 374.32),  # saśaṅkhacakraṃ
    (374.94, 395.18),  # chāyāyāṃ pārijātasya
]

cues["stotram"] = stotram_bounds()

# Phalaśruti — whisper anchors; interp values snapped to gaps where present
cues["phalashruti"] = [
    (s(1395.9, 0.6), e(1404.4, 0.9)),   # itīdaṃ
    (s(1404.4, 0.9), e(1413.9, 1.2)),   # ya idaṃ
    (s(1414.2, 0.7), e(1423.9, 1.2)),   # vedāntago
    (s(1424.2, 0.7), e(1433.9, 1.2)),   # dharmārthī
    (s(1434.2, 1.2), e(1443.6, 1.2)),   # bhaktimān
    (s(1443.9, 1.2), e(1453.5, 1.2)),   # yaśaḥ prāpnoti
    (s(1453.7, 1.2), e(1462.4, 1.2)),   # na bhayaṃ
    (s(1462.6, 1.2), e(1472.7, 1.2)),   # rogārto
    (1473.08, 1481.69),                 # durgāṇi
    (1482.15, 1490.96),                 # vāsudevāśrayo
    (1491.43, 1499.76),                 # na vāsudevabhaktānām
    (1500.20, 1508.76),                 # imaṃ stavam adhīyānaḥ
    (1509.28, 1518.02),                 # na krodho
    (1518.57, 1527.35),                 # dyauḥ sacandrārka
    (1527.88, 1535.95),                 # sasurāsura
    (1536.42, e(1545.2, 1.0)),          # indriyāṇi
    (s(1545.3, 1.0), 1555.11),          # sarvāgamānām
    (1555.51, 1564.31),                 # ṛṣayaḥ pitaro
    (1564.85, 1575.59),                 # yogo jñānaṃ
    (1576.08, 1585.92),                 # eko viṣṇur
    (1586.39, 1595.39),                 # imaṃ stavaṃ bhagavato
    (1595.88, 1611.02),                 # viśveśvaram + na te yānti oṃ nama iti
    (1611.44, 1620.06),                 # arjuna uvāca + padmapatra
    (1620.51, 1633.94),                 # śrībhagavān uvāca + yo māṃ + stuta eva tail
    (1635.32, 1649.50),                 # vyāsa uvāca + vāsanād + tail
    (1649.97, 1661.67),                 # pārvatyuvāca + kenopāyena
    (1662.23, 1696.59),                 # īśvara uvāca + śrīrāma rāma rāmeti + tail
    (1697.04, 1714.56),                 # brahmovāca + namo'stvanantāya + tail
    (1715.73, e(1726.6, 1.2)),          # sañjaya uvāca + yatra yogeśvaraḥ
    (s(1726.8, 1.2), 1739.67),          # śrībhagavān uvāca + ananyāś cintayanto
    (1740.22, 1749.33),                 # paritrāṇāya
    (1749.95, 1762.97),                 # ārtā viṣaṇṇāḥ
    (1763.60, 1777.05),                 # kāyena vācā
]

payload = {"duration": 1780.99, "cues": cues}
OUT.write_text(json.dumps(payload, indent=1))
counts = {k: len(v) for k, v in cues.items()}
print(counts)
st = cues["stotram"]
print("stotram first/last:", st[0], st[-2], st[-1])
lens = [round(b - a, 2) for a, b in st]
print("min/max śloka len:", min(lens), max(lens))
bad = [(i + 1, l) for i, l in enumerate(lens) if not 6.5 < l < 13 and i < 107]
print("odd lengths:", bad)
