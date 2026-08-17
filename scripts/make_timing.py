#!/usr/bin/env python3
"""Build mss_timing.json — exact per-verse cues for the M. S. Subbulakshmi recording.

Boundaries come from breath-gap detection (ffmpeg silencedetect) plus
whisper word-timestamp anchors, computed against the 29:41 recording
(duration 1780.99 s). Stotram śloka boundaries are aligned with dynamic
programming over the detected gaps, which fall on half-line breaths.

Inputs: /tmp/silences_fine.txt (ffmpeg silencedetect noise=-27dB d=0.18)
Run only when re-deriving cues; the JSON output is committed.
"""

import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent / "source" / "mss_timing.json"

def load_gaps(path="/tmp/silences_fine.txt"):
    gaps = []
    start = None
    for line in open(path):
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m:
            start = float(m.group(1))
            continue
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and start is not None:
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

    hits = {}  # śloka -> breath-aligned start time
    gap_ends = [e for s, e in GAPS if 400 < e < 1360]
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
    return {n: t for n, (t, _) in hits.items()}

def stotram_bounds():
    """Anchored DP: whisper anchors pin śloka starts; gap-DP fills between anchors."""
    A = 403.05          # śloka 1 start (after the long pause)
    B108 = 1352.86      # śloka 108 (vanamālī) start — verified via whisper
    cands = [(s, e) for s, e in GAPS if A + 3 < (s + e) / 2 < B108 + 2]
    mids = [(s + e) / 2 for s, e in cands]

    hits = load_anchors()
    # verified by hand against the transcript where auto-anchoring misfired
    # (whisper emitted Devanagari here, which the Latin normalizer skips)
    hits[23] = 602.5   # gururgurutamo dhāma… at 602.24
    hits[24] = 611.5   # agraṇīr grāmaṇīḥ… at 612.40
    hits[71] = 1032.6  # brahmaṇyo brahmakṛd… at 1032.88
    # snap anchor times to the nearest gap START (śloka begins after a breath)
    anchors = {1: A, 108: B108}
    for n, t in sorted(hits.items()):
        if n in (1, 108):
            continue
        best = None
        for s, e in cands:
            if abs(e - t) < 2.6 and (best is None or abs(e - t) < abs(best[1] - t)):
                best = (s, e)
        if best:
            anchors[n] = best[1]
    # enforce monotone, plausible spacing between anchors
    ordered = sorted(anchors.items())
    clean = [ordered[0]]
    for n, t in ordered[1:]:
        pn, pt = clean[-1]
        dk = n - pn
        if dk <= 0:
            continue
        per = (t - pt) / dk
        if 6.4 < per < 12.5:
            clean.append((n, t))
    if clean[-1][0] != 108:
        raise SystemExit("anchor chain must end at śloka 108")

    INF = float("inf")

    def dp_fill(t_lo, t_hi, count):
        """Choose `count` boundaries strictly inside (t_lo, t_hi) from gaps."""
        if count <= 0:
            return []
        step = (t_hi - t_lo) / (count + 1)
        pool = [(s, e) for s, e in cands if t_lo + 3 < (s + e) / 2 < t_hi - 3]
        pm = [(s + e) / 2 for s, e in pool]
        cost = [[INF] * len(pool) for _ in range(count)]
        prev = [[-1] * len(pool) for _ in range(count)]
        for i, m in enumerate(pm):
            d = m - t_lo
            if 6.4 < d < 12.5:
                cost[0][i] = abs(d - step) * 2 + abs(m - (t_lo + step)) * 0.05
        for k in range(1, count):
            target = t_lo + (k + 1) * step
            for i, m in enumerate(pm):
                for j in range(i):
                    d = m - pm[j]
                    if not (6.4 < d < 12.5) or cost[k - 1][j] == INF:
                        continue
                    c = cost[k - 1][j] + abs(d - step) * 2 + abs(m - target) * 0.05
                    if c < cost[k][i]:
                        cost[k][i] = c
                        prev[k][i] = j
        # final boundary must also lead plausibly into t_hi
        best_i, best_c = -1, INF
        for i, m in enumerate(pm):
            if cost[count - 1][i] == INF:
                continue
            d = t_hi - m
            if not (6.4 < d < 12.5):
                continue
            c = cost[count - 1][i] + abs(d - step) * 2
            if c < best_c:
                best_i, best_c = i, c
        if best_i < 0:
            # fall back to uniform interpolation inside this span
            return [("interp", t_lo + (k + 1) * step) for k in range(count)]
        picks = []
        i = best_i
        for k in range(count - 1, -1, -1):
            picks.append(i)
            i = prev[k][i]
        picks.reverse()
        return [("gap", pool[i]) for i in picks]

    # assemble all 107 boundaries (end of ślokas 1..107)
    boundary = {}  # k -> (end_time, next_start_time); boundary k = between śloka k and k+1
    for (n0, t0), (n1, t1) in zip(clean, clean[1:]):
        # anchored boundary at start of śloka n1 (except 108's handled below)
        for idx, item in enumerate(dp_fill(t0, t1, n1 - n0 - 1)):
            k = n0 + idx  # boundary between śloka k and k+1
            if item[0] == "gap":
                s, e = item[1]
                boundary[k] = (s, e)
            else:
                boundary[k] = (item[1] - 0.15, item[1] + 0.15)
        # the anchor itself: find its gap for the sing-end time
        g = None
        for s, e in cands:
            if abs(e - t1) < 0.05:
                g = (s, e)
        boundary[n1 - 1] = g if g else (t1 - 0.4, t1)
    starts = [A]
    ends = []
    for k in range(1, 108):
        s, e = boundary[k]
        ends.append(s)
        starts.append(e)
    ends.append(1395.27)  # śloka 108 ends after the vanamālī repetitions
    return [(round(a, 2), round(b, 2)) for a, b in zip(starts, ends)]

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
