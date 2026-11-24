"""Overture Maps places, read straight from the public S3 bucket (no account needed).

License: Overture places are CDLA-Permissive-2.0; a few rows carry Apache-2.0
(Foursquare) or CC0-1.0 (AllThePlaces). The per row license is kept.
Docs: https://docs.overturemaps.org/guides/places/
"""
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.fs as pafs

from . import normalize as N
from .schema import empty

BUCKET = "overturemaps-us-west-2"


def _fs():
    return pafs.S3FileSystem(anonymous=True, region="us-west-2")


def latest_release(fs=None):
    fs = fs or _fs()
    infos = fs.get_file_info(pafs.FileSelector(BUCKET + "/release/", recursive=False))
    names = sorted(i.base_name for i in infos if i.type == pafs.FileType.Directory)
    if not names:
        raise RuntimeError("no Overture releases found")
    return names[-1]


def fetch(bbox, release=None):
    """Return (release, pyarrow.Table) of places whose bbox lies inside bbox."""
    fs = _fs()
    release = release or latest_release(fs)
    path = f"{BUCKET}/release/{release}/theme=places/type=place/"
    dset = ds.dataset(path, filesystem=fs, format="parquet")
    w, s, e, n = bbox
    flt = ((pc.field("bbox", "xmin") >= w) & (pc.field("bbox", "xmax") <= e)
           & (pc.field("bbox", "ymin") >= s) & (pc.field("bbox", "ymax") <= n))
    cols = ["id", "names", "basic_category", "confidence", "websites", "emails", "socials",
            "phones", "addresses", "sources", "operating_status", "bbox"]
    return release, dset.to_table(filter=flt, columns=cols)


def records(table, min_confidence=0.0):
    for row in table.to_pylist():
        conf = row.get("confidence")
        if conf is not None and conf < min_confidence:
            continue
        r = empty()
        r["uid"] = "overture:" + row["id"]
        r["name"] = (row.get("names") or {}).get("primary")
        r["category"] = row.get("basic_category")
        addr = (row.get("addresses") or [None])[0] or {}
        r["street"] = addr.get("freeform")
        r["city"] = addr.get("locality")
        region = addr.get("region") or ""
        r["state"] = region.split("-")[-1] if region else None
        r["postcode"] = addr.get("postcode")
        r["country"] = addr.get("country")
        bb = row["bbox"]
        r["lat"] = (bb["ymin"] + bb["ymax"]) / 2
        r["lon"] = (bb["xmin"] + bb["xmax"]) / 2
        r["phone"] = N.phone((row.get("phones") or [None])[0])
        r["website"] = N.website((row.get("websites") or [None])[0])
        r["email"] = (row.get("emails") or [None])[0]
        r["socials"] = ";".join(row.get("socials") or []) or None
        r["status"] = row.get("operating_status") or "unknown"
        r["confidence"] = conf
        r["sources"] = r["uid"]
        lic = sorted({s.get("license") for s in (row.get("sources") or []) if s.get("license")})
        r["licenses"] = ";".join(lic) or "CDLA-Permissive-2.0"
        r["claim_status"] = "unclaimed"
        if r["name"]:
            yield r
