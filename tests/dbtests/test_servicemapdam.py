from transiter.data.dams import servicemapdam
from . import dbtestutil, testdata


class TestServiceMapDAM(dbtestutil.TestCase):
    def test_list_groups_and_maps_for_stops_in_route(self):
        """[Service Map DAM] List groups and maps for stops at route"""
        expected = [(testdata.service_map_group_2, testdata.service_map_2_1)]

        actual = servicemapdam.list_groups_and_maps_for_stops_in_route(
            testdata.ROUTE_TWO_PK
        )

        self.assertEqual(expected, actual)

    def test_get_default_trips_at_stops_map(self):
        """[Service Map DAM] Get default trips at stops map"""
        expected = {
            testdata.STOP_ONE_PK: {
                testdata.SERVICE_MAP_GROUP_ONE_ID: [testdata.route_one]
            },
            testdata.STOP_TWO_PK: {
                testdata.SERVICE_MAP_GROUP_ONE_ID: [
                    testdata.route_one,
                    testdata.route_two,
                ]
            },
            testdata.STOP_THREE_PK: {
                testdata.SERVICE_MAP_GROUP_ONE_ID: [testdata.route_two]
            },
            testdata.STOP_FOUR_PK: {testdata.SERVICE_MAP_GROUP_ONE_ID: []},
            testdata.STOP_FIVE_PK: {testdata.SERVICE_MAP_GROUP_ONE_ID: []},
        }
        actual = servicemapdam.get_stop_pk_to_group_id_to_routes_map(
            [
                testdata.STOP_ONE_PK,
                testdata.STOP_TWO_PK,
                testdata.STOP_THREE_PK,
                testdata.STOP_FOUR_PK,
                testdata.STOP_FIVE_PK,
            ]
        )
        self.maxDiff = None
        self.assertDictEqual(expected, actual)
