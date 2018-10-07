import unittest.mock as mock
import unittest

from transiter.endpoints import tripendpoints


class TestTripEndpoints(unittest.TestCase):

    SYSTEM_ID = '1'
    ROUTE_ID = '2'

    def test_list_all_in_route(self):
        tripendpoints.list_all_in_route(self.SYSTEM_ID,
                                        self.ROUTE_ID)

    def test_get_in_route_by_id(self):
        tripendpoints.get_in_route_by_id(self.SYSTEM_ID,
                                         self.ROUTE_ID)




