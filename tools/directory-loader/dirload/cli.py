"""Command line entry point.

  python -m dirload --region chicago --out out/chicago
  python -m dirload --bbox -87.645,41.875,-87.615,41.900 --osm-file loop.json
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys

import pyarrow as pa
import pyarrow.parquet as pq

from . import __version__, dedupe, fsq, osm, overture
from .regions import REGIONS, parse_bbox
from .schema import FIELDS

ATTRIBUTION = {
    "overture": "Overture Maps Foundation, places theme, release {release}. CDLA-Permissive-2.0 "
                "(some rows Apache-2.0 or CC0-1.0, see the licenses column). https://overturemaps.org",
    "osm": "(c) OpenStreetMap contributors. ODbL 1.0. https://www.openstreetmap.org/copyright",
    "fsq": "Foursquare Open Source Places. Apache-2.0. https://opensource.foursquare.com/os-places/",
}

COVER = ["street", "postcode", "phone", "website", "email", "socials", "opening_hours", "category"]


def coverage(rows):
    n = len(rows) or 1
    out = {"rows": len(rows)}
    for f in COVER:
        out[f] = round(sum(1 for r in rows if r.get(f)) / n, 4)
    out["multi_source"] = round(sum(1 for r in rows if ";" in (r.get("sources") or "")) / n, 4)
    by_src = {}
    for r in rows:
        for s in {x.split(":")[0] for x in r["sources"].split(";")}:
            by_src[s] = by_src.get(s, 0) + 1
    out["rows_with_source"] = by_src
    return out


def write(rows, outdir, meta):
    os.makedirs(outdir, exist_ok=True)
    cols = {f: [r.get(f) for r in rows] for f in FIELDS}
    cols["lat"] = pa.array(cols["lat"], pa.float64())
    cols["lon"] = pa.array(cols["lon"], pa.float64())
    cols["confidence"] = pa.array(cols["confidence"], pa.float64())
    table = pa.table(cols)
    pq.write_table(table, os.path.join(outdir, "places.parquet"))
    with open(os.path.join(outdir, "places.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    cov = coverage(rows)
    meta["coverage"] = cov
    with open(os.path.join(outdir, "run.json"), "w") as f:
        json.dump(meta, f, indent=2)
    lines = ["# Attribution and license for this extract", "",
             f"Built {meta['built']} by 5PM directory loader {__version__} for bbox {meta['bbox']}.", "",
             "## Sources", ""]
    for s in meta["sources"]:
        lines.append("- " + ATTRIBUTION[s].format(release=meta.get("overture_release", "?")))
    lines += ["", "## License of this file", ""]
    if "osm" in meta["sources"]:
        lines.append("This extract contains OpenStreetMap data, so the whole database is a derivative database "
                     "under the Open Database License 1.0 (ODbL). If you publish it or a database made from it, "
                     "you must keep this attribution, offer the database under ODbL, and keep it open. "
                     "https://opendatacommons.org/licenses/odbl/1-0/")
    else:
        lines.append("No OpenStreetMap rows are included. Keep the attribution above and the per row "
                     "licenses column when you share it.")
    lines += ["", "## Coverage", "", "```", json.dumps(cov, indent=2), "```", ""]
    with open(os.path.join(outdir, "ATTRIBUTION.md"), "w") as f:
        f.write("\n".join(lines))
    return cov


def main(argv=None):
    ap = argparse.ArgumentParser(prog="dirload", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--region", choices=sorted(REGIONS))
    g.add_argument("--bbox", help="west,south,east,north")
    ap.add_argument("--out", default=None, help="output folder (default out/<region or bbox>)")
    ap.add_argument("--no-overture", action="store_true")
    ap.add_argument("--overture-release", default=None, help="for example 2026-11-18.0 (default latest)")
    ap.add_argument("--min-confidence", type=float, default=0.5,
                    help="drop Overture places below this existence confidence (default 0.5)")
    ap.add_argument("--osm", action="store_true", help="fetch OSM through the Overpass API")
    ap.add_argument("--osm-endpoint", default=osm.DEFAULT_ENDPOINT)
    ap.add_argument("--osm-file", help="use a saved Overpass JSON file instead of fetching")
    ap.add_argument("--save-osm", help="also save the fetched Overpass JSON here")
    ap.add_argument("--fsq-parquet", help="path or folder of Foursquare OS Places parquet you downloaded")
    ap.add_argument("--keep-closed", action="store_true", help="keep places marked permanently closed")
    a = ap.parse_args(argv)

    bbox = REGIONS[a.region] if a.region else parse_bbox(a.bbox)
    outdir = a.out or os.path.join("out", a.region or a.bbox.replace(",", "_"))
    meta = {"built": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "bbox": list(bbox), "sources": [], "raw_counts": {}}
    recs = []
    if not a.no_overture:
        rel, t = overture.fetch(bbox, a.overture_release)
        got = list(overture.records(t, a.min_confidence))
        meta["sources"].append("overture")
        meta["overture_release"] = rel
        meta["raw_counts"]["overture"] = {"fetched": t.num_rows, "kept": len(got)}
        recs += got
        print(f"overture {rel}: {t.num_rows} fetched, {len(got)} kept", file=sys.stderr)
    if a.osm or a.osm_file:
        data = osm.load_file(a.osm_file) if a.osm_file else osm.fetch(bbox, a.osm_endpoint)
        if a.save_osm:
            os.makedirs(os.path.dirname(os.path.abspath(a.save_osm)), exist_ok=True)
            with open(a.save_osm, "w", encoding="utf-8") as f:
                json.dump(data, f)
        got = list(osm.records(data))
        meta["sources"].append("osm")
        meta["raw_counts"]["osm"] = {"fetched": len(data.get("elements", [])), "kept": len(got)}
        recs += got
        print(f"osm: {len(got)} businesses", file=sys.stderr)
    if a.fsq_parquet:
        t = fsq.fetch(a.fsq_parquet, bbox)
        got = list(fsq.records(t))
        meta["sources"].append("fsq")
        meta["raw_counts"]["fsq"] = {"fetched": t.num_rows, "kept": len(got)}
        recs += got
        print(f"fsq: {len(got)} places", file=sys.stderr)
    if not recs:
        ap.error("no records: pick at least one source")
    rows = dedupe.dedupe(recs)
    if not a.keep_closed:
        rows = [r for r in rows if r.get("status") != "permanently_closed"]
    rows.sort(key=lambda r: (r.get("postcode") or "", r["name"].lower()))
    meta["input_records"] = len(recs)
    cov = write(rows, outdir, meta)
    print(json.dumps(cov, indent=2))
    print(f"wrote {outdir}/places.parquet, places.csv, ATTRIBUTION.md, run.json", file=sys.stderr)
    return 0
