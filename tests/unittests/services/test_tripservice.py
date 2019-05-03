import unittest

from transiter import models, exceptions
from transiter.services import tripservice, links
from .. import testutil


class TestTripService(testutil.TestCase(tripservice), unittest.TestCase):
    SYSTEM_ID = "1"
    ROUTE_ID = "2"
    TRIP_ONE_ID = "3"
    TRIP_ONE_PK = 4
    TRIP_TWO_ID = "5"
    TRIP_TWO_PK = 6
    STOP_ONE_ID = "7"
    STOP_TWO_ID = "8"

    def setUp(self):
        self.tripdam = self.mockImportedModule(tripservice.tripdam)
        self.routedam = self.mockImportedModule(tripservice.routedam)

        self.route = models.Route()

        self.trip_one = models.Trip()
        self.trip_one.pk = self.TRIP_ONE_PK
        self.trip_one.id = self.TRIP_ONE_ID
        self.trip_one.route = self.route

        self.trip_two = models.Trip()
        self.trip_two.pk = self.TRIP_TWO_PK
        self.trip_two.id = self.TRIP_ONE_ID
        self.trip_two.route = self.route

        self.stop_one = models.Stop()
        self.stop_one.id = self.STOP_ONE_ID
        self.stop_two = models.Stop()
        self.stop_two.id = self.STOP_TWO_ID

    def test_list_all_in_route__route_not_found(self):
        """[Trip service] List all in route - route not found"""
        self.routedam.get_in_system_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: tripservice.list_all_in_route(self.SYSTEM_ID, self.ROUTE_ID),
        )

    def test_list_all_in_route(self):
        """[Trip service] List all trips in a route"""
        self.tripdam.list_all_in_route_by_pk.return_value = [
            self.trip_one,
            self.trip_two,
        ]
        self.tripdam.get_trip_pk_to_last_stop_map.return_value = {
            self.TRIP_ONE_PK: self.stop_one,
            self.TRIP_TWO_PK: self.stop_two,
        }

        expected = [
            {
                **self.trip_one.short_repr(),
                "last_stop": {
                    **self.stop_one.short_repr(),
                    "href": links.StopEntityLink(self.stop_one),
                },
                "href": links.TripEntityLink(self.trip_one),
            },
            {
                **self.trip_two.short_repr(),
                "last_stop": {
                    **self.stop_two.short_repr(),
                    "href": links.StopEntityLink(self.stop_two),
                },
                "href": links.TripEntityLink(self.trip_two),
            },
        ]

        actual = tripservice.list_all_in_route(self.SYSTEM_ID, self.ROUTE_ID, True)

        self.assertEqual(expected, actual)

    def test_get_in_route_by_id__trip_not_found(self):
        """[Trip service] Get in route - trip not found"""
        self.tripdam.get_in_route_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: tripservice.get_in_route_by_id(
                self.SYSTEM_ID, self.ROUTE_ID, self.TRIP_ONE_ID
            ),
        )

    def test_get_in_route_by_id(self):
        """[Trip service] Get in in route"""
        self.tripdam.get_in_route_by_id.return_value = self.trip_one

        stop_time = models.TripStopTime()
        stop_time.stop = self.stop_one
        self.trip_one.stop_times = [stop_time]

        excpected = {
            **self.trip_one.long_repr(),
            "route": {
                **self.route.short_repr(),
                "href": links.RouteEntityLink(self.route),
            },
            "stop_time_updates": [
                {
                    **stop_time.short_repr(),
                    "stop": {
                        **self.stop_one.short_repr(),
                        "href": links.StopEntityLink(self.stop_one),
                    },
                }
            ],
        }

        actual = tripservice.get_in_route_by_id(
            self.SYSTEM_ID, self.ROUTE_ID, self.TRIP_ONE_ID, True
        )

        self.maxDiff = None
        self.assertDictEqual(excpected, actual)
