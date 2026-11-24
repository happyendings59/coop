"""Merge records from all sources that describe the same place.

Candidate pairs come from neighbouring grid cells (about 125 to 165 m) and from
records sharing a phone number. A candidate pair matches when one rule fires:
  M1 same phone, under 300 m apart, names at least 0.3 similar
  M2 same website host, names at least 0.5 similar, under 150 m apart
  M3 names at least 0.8 similar, under 120 m apart
Guards:
  G1 never match two records whose house numbers differ (two branches of a chain)
  G2 inside one source only exact same names merge, because Overture and OSM
     already deduplicate themselves
  G3 across sources a pair joins only when each is the other's best match, so a
     generic record ("Northwestern Medicine") cannot chain a whole campus together
Two firms that share a reception line, or a renamed practice that kept its
number, stay separate rows; the owner claim flow sorts those out.
The merged record takes each field from the highest priority record that has
it (Overture, then OSM, then Foursquare); opening hours prefer OSM.
"""
import math
import re
from collections import defaultdict

from . import normalize as N

CELL = 0.0015  # degrees: about 165 m north-south and 125 m east-west at Chicago's latitude
PRIORITY = {"overture": 0, "osm": 1, "fsq": 2}
HOURS_PRIORITY = {"osm": 0, "fsq": 1, "overture": 2}


def meters(a, b):
    lat = math.radians((a["lat"] + b["lat"]) / 2)
    dx = (a["lon"] - b["lon"]) * 111320 * math.cos(lat)
    dy = (a["lat"] - b["lat"]) * 110540
    return math.hypot(dx, dy)


def _housenum(street):
    m = re.match(r"\s*(\d+)", street or "")
    return m.group(1) if m else None


def conflict(a, b):
    """True when both records carry a house number and the numbers differ (two branches)."""
    return bool(a["_hn"] and b["_hn"] and a["_hn"] != b["_hn"])


def score(a, b):
    """Match score 0..1 for a candidate pair, 0 when no rule fires."""
    if conflict(a, b):
        return 0.0
    d = meters(a, b)
    if d > 300:
        return 0.0
    sim = N.name_similar(a["_nk"], b["_nk"])
    best = 0.0
    if a["phone"] and a["phone"] == b["phone"] and sim >= 0.3:  # M1
        best = max(best, 0.7 + 0.3 * sim)
    if d <= 150 and sim >= 0.5 and a["_host"] and a["_host"] == b["_host"]:  # M2
        best = max(best, 0.6 + 0.3 * sim)
    if d <= 120 and sim >= 0.8:  # M3
        best = max(best, 0.5 + 0.4 * sim)
    return best and best - d / 3000  # nearer wins a tie


class _UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, i):
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def _src(r):
    return r["uid"].split(":", 1)[0]


def _rank(r):
    conf = r.get("confidence")
    return (PRIORITY.get(_src(r), 9), -(conf if conf is not None else 0.5))


def merge_group(group):
    group = sorted(group, key=_rank)
    out = dict(group[0])
    for r in group[1:]:
        for k, v in r.items():
            if out.get(k) in (None, "", "unknown") and v not in (None, ""):
                out[k] = v
    with_hours = sorted((r for r in group if r.get("opening_hours")),
                        key=lambda r: HOURS_PRIORITY.get(_src(r), 9))
    out["opening_hours"] = with_hours[0]["opening_hours"] if with_hours else None
    if any(r.get("status") == "permanently_closed" and _src(r) == "overture" for r in group):
        out["status"] = "permanently_closed"
    out["sources"] = ";".join(sorted({s for r in group for s in r["sources"].split(";")}))
    out["licenses"] = ";".join(sorted({s for r in group for s in r["licenses"].split(";")}))
    return out


def dedupe(records):
    recs = [dict(r) for r in records if r.get("lat") is not None and r.get("name")]
    for r in recs:
        r["_nk"] = N.name_key(r["name"])
        r["_host"] = N.host(r["website"])
        r["_hn"] = _housenum(r["street"])
    grid = defaultdict(list)
    for i, r in enumerate(recs):
        grid[(int(r["lat"] // CELL), int(r["lon"] // CELL))].append(i)
    uf = _UF(len(recs))
    # Candidate pairs: neighbouring grid cells, plus same phone number anywhere nearby.
    cand = set()
    for (cy, cx), idxs in grid.items():
        neigh = [j for dy in (-1, 0, 1) for dx in (-1, 0, 1) for j in grid.get((cy + dy, cx + dx), ())]
        for i in idxs:
            for j in neigh:
                if j > i:
                    cand.add((i, j))
    by_phone = defaultdict(list)
    for i, r in enumerate(recs):
        if r["phone"]:
            by_phone[r["phone"]].append(i)
    for idxs in by_phone.values():
        if len(idxs) <= 10:  # more than 10 is a shared switchboard or chain line
            cand.update((a, b) for a in idxs for b in idxs if a < b)
    # Same source: Overture and OSM already deduplicate themselves, so only merge
    # exact same name key. Different sources: keep each record's single best
    # partner per other source and join mutual best pairs only, so one generic
    # record ("Northwestern Medicine") cannot pull a whole campus into one row.
    best = {}
    for i, j in cand:
        a, b = recs[i], recs[j]
        if _src(a) == _src(b):
            if a["_nk"] and a["_nk"] == b["_nk"] and not conflict(a, b) and meters(a, b) <= 120:
                uf.union(i, j)
            continue
        sc = score(a, b)
        if sc <= 0:
            continue
        for x, y in ((i, j), (j, i)):
            key = (x, _src(recs[y]))
            if sc > best.get(key, (0, None))[0]:
                best[key] = (sc, y)
    for (x, src), (sc, y) in best.items():
        if y > x and best.get((y, _src(recs[x])), (0, None))[1] == x:
            uf.union(x, y)
    groups = defaultdict(list)
    for i, r in enumerate(recs):
        groups[uf.find(i)].append(r)
    merged = []
    for g in groups.values():
        m = merge_group(g)
        m.pop("_nk", None)
        m.pop("_host", None)
        m.pop("_hn", None)
        merged.append(m)
    return merged
