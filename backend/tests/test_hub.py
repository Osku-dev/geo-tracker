from app.hub import _point_in_bbox, parse_bbox_query


class TestPointInBbox:
    def test_point_inside_bbox(self):
        bbox = (0.0, 0.0, 10.0, 10.0)
        assert _point_in_bbox(5.0, 5.0, bbox) is True

    def test_point_outside_bbox_lon(self):
        bbox = (0.0, 0.0, 10.0, 10.0)
        assert _point_in_bbox(11.0, 5.0, bbox) is False

    def test_point_outside_bbox_lat(self):
        bbox = (0.0, 0.0, 10.0, 10.0)
        assert _point_in_bbox(5.0, -1.0, bbox) is False

    def test_boundary_is_inclusive(self):
        bbox = (0.0, 0.0, 10.0, 10.0)
        assert _point_in_bbox(0.0, 0.0, bbox) is True
        assert _point_in_bbox(10.0, 10.0, bbox) is True
        

class TestParseBboxQuery:
    def test_valid_bbox_parses_correctly(self):
        result = parse_bbox_query("0", "1", "2", "3")
        assert result == (0.0, 1.0, 2.0, 3.0)

    def test_returns_none_if_any_value_missing(self):
        assert parse_bbox_query(None, "1", "2", "3") is None
        assert parse_bbox_query("0", None, "2", "3") is None
        assert parse_bbox_query("0", "1", None, "3") is None
        assert parse_bbox_query("0", "1", "2", None) is None

    def test_returns_none_if_invalid_float(self):
        result = parse_bbox_query("abc", "1", "2", "3")
        assert result is None

    def test_accepts_whitespace_strings(self):
        result = parse_bbox_query(" 0 ", " 1 ", " 2 ", " 3 ")
        assert result == (0.0, 1.0, 2.0, 3.0)