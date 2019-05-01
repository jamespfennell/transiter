from transiter.data.dams import servicemapdam
from . import dbtestutil, testdata


class TestServiceMapDAM(dbtestutil.TestCase):
    def test__servicepatterndata__get_default_trips_at_stops_map(self):
        """[Service Map DAM] Get default trips at stops map"""
        actual = servicemapdam.get_stop_pk_to_group_id_to_routes_map(
            [
                testdata.STOP_ONE_PK,
                testdata.STOP_TWO_PK,
                testdata.STOP_THREE_PK,
                testdata.STOP_FOUR_PK,
                testdata.STOP_FIVE_PK,
            ]
        )

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

        self.maxDiff = None
        self.assertDictEqual(expected, actual)
