"""The one record shape every source is mapped into (see docs/DESIGN.md, section 4)."""

FIELDS = [
    "uid",            # stable id for this directory: <source>:<source id> of the record kept as primary
    "name",
    "category",       # free text category from the source (Overture basic_category, OSM tag, FSQ label)
    "street", "city", "state", "postcode", "country",
    "lat", "lon",
    "phone",          # E.164 where the source gives it
    "website",
    "email",          # public business email only, as published by the source
    "socials",        # semicolon separated URLs
    "opening_hours",  # OSM opening_hours syntax, see https://wiki.openstreetmap.org/wiki/Key:opening_hours
    "status",         # open, permanently_closed, temporarily_closed, unknown
    "confidence",     # 0..1, Overture's existence confidence when known
    "sources",        # semicolon separated <source>:<id> for every record merged into this one
    "licenses",       # semicolon separated licenses of the merged records
    "claim_status",   # always "unclaimed" from the loader; the claim service changes it
]


def empty():
    return {f: None for f in FIELDS}
