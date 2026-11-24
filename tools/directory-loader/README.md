# Directory loader

Builds an open "yellow pages" extract of businesses for a region from data that may legally be reused in bulk: **Overture Maps places**, **OpenStreetMap** (the source of opening hours) and, optionally, **Foursquare Open Source Places**. It never touches Google Maps, Yelp, Yellow Pages or LinkedIn. The requirements it implements are in [spec/directory.md](../../spec/directory.md) §6.1.

Reuse first: it reads Overture's public parquet files directly (the same files the official [overturemaps-py](https://github.com/OvertureMaps/overturemaps-py) tool reads) and OSM through the public [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API); the only new code is the mapping, the deduper and the attribution.

## Run it

```
cd tools/directory-loader
pip install -r requirements.txt
python -m dirload --region chicago --osm            # Overture + OSM, about 2 minutes
python -m dirload --region chicago-loop --osm       # small test box
python -m dirload --bbox -87.70,41.87,-87.60,41.92  # any box: west,south,east,north
python -m dirload --region chicago --fsq-parquet ~/fsq-os-places/   # add Foursquare
```

Or run the **directory-build** GitHub workflow (Actions tab, "Run workflow"); it runs the tests, builds the extract and attaches it to the run as a download.

Options: `--min-confidence` (default 0.5, Overture's estimate that the place exists), `--keep-closed`, `--overture-release`, `--osm-file` (reuse a saved Overpass response), `--save-osm`.

## Output (`out/<region>/`)

| File | What |
| --- | --- |
| `places.parquet`, `places.csv` | one row per place, fields in `dirload/schema.py` |
| `ATTRIBUTION.md` | sources, licenses, and coverage; keep it with any copy |
| `run.json` | release used, bbox, counts, coverage |

## License of the data

Overture rows are CDLA-Permissive-2.0 (a few Apache-2.0 or CC0-1.0, see the `licenses` column). Foursquare rows are Apache-2.0. **When OSM rows are included, the extract is a derivative database under ODbL 1.0**: share it under ODbL with "© OpenStreetMap contributors". The loader code itself is AGPL-3.0 like the rest of this repository.

## How duplicates are merged

See the docstring at the top of `dirload/dedupe.py`. In short: same phone, same website, or near identical names, all within a short distance; never across different house numbers; one generic record cannot swallow a campus.

## Chicago, first run (2026-11-24, Overture only)

177,185 places after dropping low confidence and closed ones. Street address 98.7%, phone 87.5%, website 78.9%, category 97.5%, socials 44.7%, public email 27.7%, opening hours 0% (Overture has none; OSM adds them).

## Tests

```
python -m unittest discover -s tests -v
```
