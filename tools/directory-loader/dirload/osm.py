"""OpenStreetMap businesses via the Overpass API, or from a saved Overpass JSON file.

OSM is the main free source of opening hours. License: ODbL 1.0. Any database
that mixes OSM rows with other rows is a derivative database and must be shared
under ODbL with attribution "(c) OpenStreetMap contributors" (see docs/DESIGN.md, section 6).
Overpass usage policy: https://dev.overpass-api.de/overpass-doc/en/preface/commons.html
(one query at a time, keep it under about 10,000 queries a day, identify your client).
"""
import json
import urllib.parse
import urllib.request

from . import normalize as N
from .schema import empty

DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"
CATEGORY_KEYS = ["shop", "amenity", "office", "craft", "healthcare", "tourism", "leisure", "club"]
# amenity values that are infrastructure, not businesses
SKIP_AMENITY = {"bench", "parking", "parking_space", "parking_entrance", "bicycle_parking", "waste_basket",
                "recycling", "drinking_water", "toilets", "shelter", "post_box", "vending_machine",
                "telephone", "fountain", "charging_station", "bicycle_rental", "atm", "clock",
                "loading_dock", "grit_bin", "motorcycle_parking", "taxi", "hunting_stand", "waste_disposal"}
SKIP_LEISURE = {"park", "pitch", "playground", "garden", "swimming_pool", "track", "nature_reserve",
                "dog_park", "picnic_table", "common", "slipway", "outdoor_seating"}


def query(bbox, timeout=180):
    w, s, e, n = bbox
    b = f"{s},{w},{n},{e}"
    parts = "".join(f'nwr["{k}"]["name"]({b});' for k in CATEGORY_KEYS)
    return f"[out:json][timeout:{timeout}];({parts});out center tags;"


def fetch(bbox, endpoint=DEFAULT_ENDPOINT, user_agent="5pm-coop-directory-loader/0.1"):
    data = urllib.parse.urlencode({"data": query(bbox)}).encode()
    req = urllib.request.Request(endpoint, data=data, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.load(resp)


def load_file(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _category(tags):
    for k in CATEGORY_KEYS:
        v = tags.get(k)
        if v:
            if k == "amenity" and v in SKIP_AMENITY:
                return None
            if k == "leisure" and v in SKIP_LEISURE:
                return None
            return f"{k}={v}"
    return None


def records(overpass_json):
    for el in overpass_json.get("elements", []):
        tags = el.get("tags") or {}
        cat = _category(tags)
        if not cat or not tags.get("name"):
            continue
        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            c = el.get("center") or {}
            lat, lon = c.get("lat"), c.get("lon")
        if lat is None:
            continue
        r = empty()
        r["uid"] = f"osm:{el['type']}/{el['id']}"
        r["name"] = tags["name"]
        r["category"] = cat
        hn, st = tags.get("addr:housenumber"), tags.get("addr:street")
        r["street"] = " ".join(x for x in (hn, st) if x) or None
        if tags.get("addr:unit"):
            r["street"] = (r["street"] or "") + " Unit " + tags["addr:unit"]
        r["city"] = tags.get("addr:city")
        r["state"] = tags.get("addr:state")
        r["postcode"] = tags.get("addr:postcode")
        r["country"] = tags.get("addr:country")
        r["lat"], r["lon"] = lat, lon
        r["phone"] = N.phone(tags.get("phone") or tags.get("contact:phone"))
        r["website"] = N.website(tags.get("website") or tags.get("contact:website") or tags.get("url"))
        r["email"] = tags.get("email") or tags.get("contact:email")
        soc = [tags[k] for k in ("contact:facebook", "contact:instagram", "contact:twitter") if tags.get(k)]
        r["socials"] = ";".join(soc) or None
        r["opening_hours"] = tags.get("opening_hours")
        if tags.get("disused:shop") or tags.get("abandoned") == "yes":
            r["status"] = "permanently_closed"
        else:
            r["status"] = "unknown"
        r["sources"] = r["uid"]
        r["licenses"] = "ODbL-1.0"
        r["claim_status"] = "unclaimed"
        yield r
