import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dirload import dedupe, normalize as N, osm  # noqa: E402
from dirload.regions import parse_bbox  # noqa: E402
from dirload.schema import empty  # noqa: E402


def rec(uid, name, lat, lon, **kw):
    r = empty()
    r.update(uid=uid, name=name, lat=lat, lon=lon, sources=uid,
             licenses="ODbL-1.0" if uid.startswith("osm") else "CDLA-Permissive-2.0")
    r.update(kw)
    return r


class Normalize(unittest.TestCase):
    def test_phone(self):
        self.assertEqual(N.phone("(312) 555-0100"), "+13125550100")
        self.assertEqual(N.phone("1-312-555-0100"), "+13125550100")
        self.assertEqual(N.phone("+44 20 7946 0958"), "+442079460958")
        self.assertIsNone(N.phone("555-0100"))
        self.assertIsNone(N.phone(None))

    def test_website_and_host(self):
        self.assertEqual(N.website("example.com"), "http://example.com")
        self.assertEqual(N.host("https://www.Example.com/menu"), "example.com")

    def test_names(self):
        self.assertEqual(N.name_key("The Joe's Pizza & Grill, Inc."), "joes pizza grill")
        self.assertGreaterEqual(N.name_similar("joes pizza", "joes pizza bar"), 0.85)
        self.assertLess(N.name_similar("northwestern", "northwestern medicine cardiology"), 0.5)

    def test_bbox(self):
        self.assertEqual(parse_bbox("-88,41,-87,42"), (-88.0, 41.0, -87.0, 42.0))
        with self.assertRaises(ValueError):
            parse_bbox("-87,41,-88,42")


class Osm(unittest.TestCase):
    def test_records(self):
        data = {"elements": [
            {"type": "node", "id": 1, "lat": 41.88, "lon": -87.63,
             "tags": {"name": "Joe's Pizza", "amenity": "restaurant", "addr:housenumber": "10",
                      "addr:street": "W Madison St", "phone": "312-555-0100",
                      "opening_hours": "Mo-Su 11:00-22:00"}},
            {"type": "way", "id": 2, "center": {"lat": 41.9, "lon": -87.6},
             "tags": {"name": "Some Bench", "amenity": "bench"}},
            {"type": "node", "id": 3, "lat": 41.9, "lon": -87.6, "tags": {"shop": "bakery"}},
        ]}
        out = list(osm.records(data))
        self.assertEqual(len(out), 1)
        r = out[0]
        self.assertEqual(r["uid"], "osm:node/1")
        self.assertEqual(r["street"], "10 W Madison St")
        self.assertEqual(r["phone"], "+13125550100")
        self.assertEqual(r["opening_hours"], "Mo-Su 11:00-22:00")
        self.assertEqual(r["category"], "amenity=restaurant")

    def test_query_has_bbox_in_overpass_order(self):
        self.assertIn("(41.0,-88.0,42.0,-87.0)", osm.query((-88.0, 41.0, -87.0, 42.0)))


class Dedupe(unittest.TestCase):
    def test_cross_source_merge_takes_osm_hours(self):
        a = rec("overture:a", "Joe's Pizza", 41.88000, -87.63000, street="10 W Madison St",
                phone="+13125550100", website="https://joespizza.example", confidence=0.9)
        b = rec("osm:node/1", "Joes Pizza", 41.88030, -87.63010, street="10 W Madison St",
                opening_hours="Mo-Su 11:00-22:00")
        out = dedupe.dedupe([a, b])
        self.assertEqual(len(out), 1)
        m = out[0]
        self.assertEqual(m["uid"], "overture:a")
        self.assertEqual(m["opening_hours"], "Mo-Su 11:00-22:00")
        self.assertEqual(m["sources"], "osm:node/1;overture:a")
        self.assertEqual(m["licenses"], "CDLA-Permissive-2.0;ODbL-1.0")

    def test_two_branches_stay_apart(self):
        a = rec("overture:a", "Mattress Firm", 41.880, -87.630, street="4004 Roosevelt Rd")
        b = rec("osm:node/2", "Mattress Firm", 41.8805, -87.630, street="1137 S Mannheim Rd")
        self.assertEqual(len(dedupe.dedupe([a, b])), 2)

    def test_far_apart_same_name_stays_apart(self):
        a = rec("overture:a", "Joe's Pizza", 41.88, -87.63)
        b = rec("osm:node/1", "Joe's Pizza", 41.90, -87.63)
        self.assertEqual(len(dedupe.dedupe([a, b])), 2)

    def test_generic_name_does_not_chain(self):
        hub = rec("osm:node/9", "Northwestern Medicine", 41.8950, -87.6200)
        docs = [rec(f"overture:{i}", f"Dr {n} MD Northwestern Medicine", 41.8950, -87.6201,
                    website="https://nm.org") for i, n in enumerate(["Ann Lee", "Bo Diaz", "Cy Oh"])]
        out = dedupe.dedupe([hub] + docs)
        self.assertGreaterEqual(len(out), 3)

    def test_shared_phone_different_firms_stay_apart(self):
        a = rec("overture:a", "Bubon Orthodontics", 41.88, -87.63, phone="+13125550100")
        b = rec("osm:node/1", "Diamond Plus Dental", 41.88, -87.63, phone="+13125550100")
        self.assertEqual(len(dedupe.dedupe([a, b])), 2)

    def test_same_source_exact_duplicate_merges(self):
        a = rec("overture:a", "Cumberland", 41.98, -87.83, street="5800 N Cumberland Ave")
        b = rec("overture:b", "Cumberland", 41.98, -87.8301, street="5800 N Cumberland Ave")
        self.assertEqual(len(dedupe.dedupe([a, b])), 1)


if __name__ == "__main__":
    unittest.main()
