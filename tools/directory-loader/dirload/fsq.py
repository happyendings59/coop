"""Foursquare Open Source Places from a parquet file you downloaded yourself.

License: Apache-2.0. Since 2025 Foursquare serves the files through a free,
gated download (Hugging Face dataset foursquare/fsq-os-places, or the Foursquare
portal), so this loader reads a local copy instead of fetching it.
Docs: https://docs.foursquare.com/data-products/docs/access-fsq-os-places
Overture already includes many Foursquare rows, so this source is optional.
"""
import pyarrow.compute as pc
import pyarrow.dataset as ds

from . import normalize as N
from .schema import empty


def fetch(path, bbox):
    dset = ds.dataset(path, format="parquet")
    w, s, e, n = bbox
    flt = ((pc.field("longitude") >= w) & (pc.field("longitude") <= e)
           & (pc.field("latitude") >= s) & (pc.field("latitude") <= n))
    return dset.to_table(filter=flt)


def records(table):
    names = set(table.column_names)
    for row in table.to_pylist():
        if not row.get("name") or row.get("latitude") is None:
            continue
        r = empty()
        r["uid"] = "fsq:" + str(row.get("fsq_place_id") or row.get("fsq_id"))
        r["name"] = row["name"]
        labels = row.get("fsq_category_labels") if "fsq_category_labels" in names else None
        r["category"] = labels[0] if labels else None
        r["street"] = row.get("address")
        r["city"] = row.get("locality")
        r["state"] = row.get("region")
        r["postcode"] = row.get("postcode")
        r["country"] = row.get("country")
        r["lat"], r["lon"] = row["latitude"], row["longitude"]
        r["phone"] = N.phone(row.get("tel"))
        r["website"] = N.website(row.get("website"))
        r["email"] = row.get("email")
        soc = []
        if row.get("facebook_id"):
            soc.append(f"https://www.facebook.com/{row['facebook_id']}")
        if row.get("instagram"):
            soc.append(f"https://www.instagram.com/{row['instagram']}")
        if row.get("twitter"):
            soc.append(f"https://x.com/{row['twitter']}")
        r["socials"] = ";".join(soc) or None
        r["status"] = "permanently_closed" if row.get("date_closed") else "unknown"
        r["sources"] = r["uid"]
        r["licenses"] = "Apache-2.0"
        r["claim_status"] = "unclaimed"
        yield r
