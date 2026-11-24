"""Named regions as bounding boxes (west, south, east, north), WGS84 degrees."""

REGIONS = {
    # City of Chicago plus the first ring of suburbs.
    "chicago": (-87.94, 41.64, -87.52, 42.03),
    # A small Loop / Near North test box, fast for trying the tool.
    "chicago-loop": (-87.645, 41.875, -87.615, 41.900),
}


def parse_bbox(text):
    parts = [float(p) for p in text.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be west,south,east,north")
    w, s, e, n = parts
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
        raise ValueError("bbox out of range or reversed")
    return w, s, e, n
