import pytest

from app.schemas import GISContext
from app.services.gis import GISEngine, bearing_deg, haversine_m, parse_voltages


class TestVoltageTagParsing:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("115000", [115_000]),
            ("12470;4160", [12_470, 4_160]),
            ("69 kV", [69_000]),
            ("230", [230_000]),  # bare kV without a unit
            ("400000;220000", [400_000, 220_000]),
            ("", []),
            (None, []),
            ("not a voltage", []),
        ],
    )
    def test_parses_the_shapes_osm_actually_contains(self, raw, expected):
        assert parse_voltages(raw) == expected

    def test_results_are_deduplicated_and_descending(self):
        assert parse_voltages("12470;12470;4160") == [12_470, 4_160]


class TestGeodesy:
    def test_haversine_matches_a_known_distance(self):
        # San Francisco City Hall to the Ferry Building, ~2.6 km.
        distance = haversine_m(37.7793, -122.4193, 37.7955, -122.3937)
        assert 2_400 < distance < 2_900

    def test_zero_distance(self):
        assert haversine_m(37.0, -122.0, 37.0, -122.0) == pytest.approx(0.0, abs=1e-6)

    def test_bearing_cardinal_directions(self):
        assert bearing_deg(37.0, -122.0, 38.0, -122.0) == pytest.approx(0.0, abs=0.5)
        assert bearing_deg(37.0, -122.0, 37.0, -121.0) == pytest.approx(90.0, abs=0.5)
        assert bearing_deg(37.0, -122.0, 36.0, -122.0) == pytest.approx(180.0, abs=0.5)


class TestOverpassParsing:
    def test_parses_elements_and_computes_distance(self):
        payload = {
            "elements": [
                {
                    "type": "way",
                    "id": 1,
                    "center": {"lat": 37.7750, "lon": -122.4194},
                    "tags": {
                        "power": "minor_line",
                        "voltage": "12470",
                        "operator": "Pacific Gas and Electric Company",
                        "ref": "1234",
                    },
                },
                {
                    "type": "node",
                    "id": 2,
                    "lat": 37.7760,
                    "lon": -122.4194,
                    "tags": {"power": "pole"},
                },
                {"type": "node", "id": 3, "lat": 37.7749, "lon": -122.4194, "tags": {"highway": "stop"}},
            ]
        }
        assets = GISEngine()._parse_overpass(payload, 37.7749, -122.4194)
        assert len(assets) == 2, "non-power elements must be dropped"

        line = assets[0]
        assert line.asset_kind == "minor_line"
        assert line.voltage_v == [12_470]
        assert line.operator == "Pacific Gas and Electric Company"
        assert line.distance_m is not None and line.distance_m < 20

    def test_way_geometry_becomes_a_drawable_line(self):
        """`out body geom` gives every node; without it a line is just a dot."""
        payload = {
            "elements": [
                {
                    "type": "way",
                    "id": 42,
                    "tags": {"power": "line", "voltage": "115000"},
                    "geometry": [
                        {"lat": 37.7749, "lon": -122.4194},
                        {"lat": 37.7755, "lon": -122.4180},
                        {"lat": 37.7761, "lon": -122.4166},
                    ],
                }
            ]
        }
        asset = GISEngine()._parse_overpass(payload, 37.7749, -122.4194)[0]
        assert asset.geometry is not None
        assert asset.geometry["type"] == "MultiLineString"
        assert len(asset.geometry["coordinates"][0]) == 3
        # GeoJSON is lon/lat, not lat/lon — getting this backwards puts San
        # Francisco in the Southern Ocean.
        assert asset.geometry["coordinates"][0][0] == [-122.4194, 37.7749]
        # With no explicit centre, the midpoint stands in for distance sorting.
        assert asset.latitude is not None and asset.longitude is not None

    def test_a_single_node_way_is_not_drawn_as_a_line(self):
        payload = {
            "elements": [
                {
                    "type": "way",
                    "id": 43,
                    "tags": {"power": "line"},
                    "geometry": [{"lat": 37.7749, "lon": -122.4194}],
                }
            ]
        }
        asset = GISEngine()._parse_overpass(payload, 37.7749, -122.4194)[0]
        assert asset.geometry["type"] == "Point"

    def test_nodes_without_geometry_still_parse(self):
        payload = {
            "elements": [
                {"type": "node", "id": 44, "lat": 37.775, "lon": -122.419, "tags": {"power": "pole"}}
            ]
        }
        asset = GISEngine()._parse_overpass(payload, 37.7749, -122.4194)[0]
        assert asset.geometry is None
        assert asset.asset_kind == "pole"

    def test_utility_pole_man_made_tag_is_recognised(self):
        payload = {
            "elements": [
                {
                    "type": "node",
                    "id": 7,
                    "lat": 37.7749,
                    "lon": -122.4194,
                    "tags": {"man_made": "utility_pole"},
                }
            ]
        }
        assets = GISEngine()._parse_overpass(payload, 37.7749, -122.4194)
        assert len(assets) == 1
        assert assets[0].asset_kind == "pole"


class TestArcGISParsing:
    def test_hifld_voltage_is_treated_as_kilovolts(self):
        payload = {
            "features": [
                {
                    "attributes": {"OBJECTID": 5, "VOLTAGE": 230, "OWNER": "PacifiCorp"},
                    "geometry": {"paths": [[[-122.42, 37.77], [-122.41, 37.78]]]},
                }
            ]
        }
        assets = GISEngine()._parse_arcgis(payload, 37.7749, -122.4194, "hifld_transmission", "line")
        assert assets[0].voltage_v == [230_000]
        assert assets[0].operator == "PacifiCorp"
        assert assets[0].geometry["type"] == "MultiLineString"

    def test_sentinel_values_are_discarded(self):
        payload = {
            "features": [
                {
                    "attributes": {"OBJECTID": 6, "VOLTAGE": -999999, "OWNER": "NOT AVAILABLE"},
                    "geometry": {"x": -122.42, "y": 37.77},
                }
            ]
        }
        assets = GISEngine()._parse_arcgis(payload, 37.7749, -122.4194, "hifld_transmission", "line")
        assert assets[0].voltage_v == []
        assert assets[0].operator is None


class TestFinalise:
    def test_nearest_of_each_kind_is_selected_and_operators_ranked(self):
        engine = GISEngine()
        payload = {
            "elements": [
                {
                    "type": "way",
                    "id": 1,
                    "center": {"lat": 37.7760, "lon": -122.4194},
                    "tags": {"power": "line", "operator": "Utility A", "voltage": "115000"},
                },
                {
                    "type": "way",
                    "id": 2,
                    "center": {"lat": 37.7751, "lon": -122.4194},
                    "tags": {"power": "minor_line", "operator": "Utility B"},
                },
                {
                    "type": "node",
                    "id": 3,
                    "lat": 37.7752,
                    "lon": -122.4194,
                    "tags": {"power": "substation", "operator": "Utility B"},
                },
            ]
        }
        assets = engine._parse_overpass(payload, 37.7749, -122.4194)
        context = GISContext(query_latitude=37.7749, query_longitude=-122.4194, radius_m=400, assets=assets)
        engine._finalise(context)

        assert context.nearest_line.element_id == "2"
        assert context.nearest_substation.element_id == "3"
        assert context.operators[0] == "Utility B"
        assert context.voltages_v == [115_000]
