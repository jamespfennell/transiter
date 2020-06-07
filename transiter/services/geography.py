from math import *

RADIUS_OF_EARTH_IN_METERS = 6371000.0


def distance(lat_1: float, lon_1: float, lat_2: float, lon_2: float) -> float:
    """
    Calculate the distance in meters between two points on the Earth.
    """
    return RADIUS_OF_EARTH_IN_METERS * acos(
        cos(radians(lon_1 - lon_2)) * cos(radians(lat_1)) * cos(radians(lat_2))
        + sin(radians(lat_1)) * sin(radians(lat_2))
    )


def longitude_bounds(lat: float, lon: float, max_distance: float):
    """
    Calculate the longitude bounds a point can have in order to be at a certain
    distance to a reference point.
    """
    assert max_distance >= 0
    delta = degrees(
        abs(
            acos(
                (
                    cos(max_distance * 1.02 / RADIUS_OF_EARTH_IN_METERS)
                    - sin(radians(lat)) ** 2
                )
                / (cos(radians(lat)) ** 2)
            )
        )
    )
    return lon - delta, lon + delta


def latitude_bounds(lat: float, lon: float, max_distance: float):
    """
    Calculate the latitude bounds a point can have in order to be at a certain
    distance to a reference point.
    """
    assert max_distance >= 0
    return lat - max_distance * 1.02, lat + max_distance * 1.02
