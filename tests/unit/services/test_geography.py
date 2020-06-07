from transiter.services import geography
import pytest


@pytest.mark.parametrize("delta", [-4.3, -0.1, 0.1, 4.3])
@pytest.mark.parametrize("lon", [-150, -50, 0, 50, 150])
@pytest.mark.parametrize("lat", [-75, -7.4, 0, 7.4, 75])
class TestBounds:
    def test_latitude_bounds(self, delta, lat, lon):
        distance = geography.distance(lat, lon, lat + delta, lon)

        lower_bound, upper_bound = geography.latitude_bounds(lat, lon, distance)

        assert lower_bound <= lat - delta
        assert upper_bound >= lat + delta

    def test_longitude_bounds(self, delta, lat, lon):

        distance = geography.distance(lat, lon, lat, lon + delta)

        lower_bound, upper_bound = geography.longitude_bounds(lat, lon, distance)

        assert lower_bound <= lon - delta
        assert upper_bound >= lon + delta
