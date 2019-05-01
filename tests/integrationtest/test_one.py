import subprocess
import time
import requests
import json
import unittest

import gtfsrealtimegenerator


class IntegrationTest(unittest.TestCase):

    TRANSITER_URL = "http://localhost:5000/"

    STOP_IDS = {
        "1A",
        "1B",
        "1C",
        "1D",
        "1E",
        "1F",
        "1G",
        "1AS",
        "1BS",
        "1CS",
        "1DS",
        "1ES",
        "1FS",
        "1GS",
        "1AN",
        "1BN",
        "1CN",
        "1DN",
        "1EN",
        "1FN",
        "1GN",
    }
    ROUTE_IDS = {"A", "B"}
    FEED_IDS = ["GtfsRealtimeFeed", "gtfsstatic"]
    STOP_ID_TO_USUAL_ROUTES = {
        "1A": ["A"],
        "1B": [],
        "1C": [],
        "1D": ["A"],
        "1E": ["A"],
        "1F": [],
        "1G": ["A"],
    }
    ROUTE_ID_TO_USUAL_ROUTE = {"A": ["1A", "1D", "1E", "1G"], "B": []}

    @classmethod
    def setUpClass(cls):
        startup_http_services()

    @classmethod
    def tearDownClass(cls):
        shutdown_http_services()

    def test_000_check_for_no_systems(self):
        response = self._get("systems")
        self.assertEqual(response, [])

    def test_006_install_system_success(self):
        with open("output/gtfsstaticdata.zip", "rb") as zip_file:
            zip_file_data = zip_file.read()

        requests.put("http://localhost:5001", data=zip_file_data)

        files = {"config_file": open("data/system-config.toml", "rb")}
        response = self._put("systems/testsystem", files=files)
        response.raise_for_status()

    def test_010_count_stops(self):
        system_response = self._get("systems/testsystem")
        stops_count = system_response["stops"]["count"]
        self.assertEqual(len(self.STOP_IDS), stops_count)

    def test_010_get_stop_ids(self):
        stops_response = self._get("systems/testsystem/stops")
        actual_stop_ids = set([stop["id"] for stop in stops_response])
        self.assertEqual(self.STOP_IDS, actual_stop_ids)

    def test_011_count_feeds(self):
        system_response = self._get("systems/testsystem")
        feeds_count = system_response["feeds"]["count"]
        self.assertEqual(len(self.FEED_IDS), feeds_count)

    def test_011_get_feed_ids(self):
        feeds_response = self._get("systems/testsystem/feeds")
        actual_feed_ids = set([feed["id"] for feed in feeds_response])
        self.assertSetEqual(set(self.FEED_IDS), actual_feed_ids)

    def test_011_count_routes(self):
        system_response = self._get("systems/testsystem")
        routes_count = system_response["routes"]["count"]
        self.assertEqual(len(self.ROUTE_IDS), routes_count)

    def test_011_get_route_ids(self):
        routes_response = self._get("systems/testsystem/routes")
        actual_route_ids = set([route["id"] for route in routes_response])
        self.assertEqual(self.ROUTE_IDS, actual_route_ids)

    def test_012_all_stops_have_no_trips(self):
        for stop_id in self.STOP_IDS:
            stop_response = self._get("systems/testsystem/stops/{}".format(stop_id))
            self.assertEqual([], stop_response["stop_time_updates"])

    def test_013_stop_usual_routes(self):
        for stop_id, usual_route in self.STOP_ID_TO_USUAL_ROUTES.items():
            stop_response = self._get("systems/testsystem/stops/{}".format(stop_id))
            if len(stop_response["service_maps"]) == 0:
                actual = []
            else:
                actual = [
                    route["id"] for route in stop_response["service_maps"][0]["routes"]
                ]
            self.assertListEqual(usual_route, actual)

    def test_014_route_usual_stops(self):
        for route_id, usual_stops in self.ROUTE_ID_TO_USUAL_ROUTE.items():
            route_response = self._get("systems/testsystem/routes/{}".format(route_id))
            for service_map in route_response["service_maps"]:
                if service_map["group_id"] != "any_time":
                    continue
                actual_stops = [stop["id"] for stop in service_map["stops"]]
                self.assertListEqual(usual_stops, actual_stops)
                break

    # TODO: re-enable this when realtime service maps are a thing
    # def test_014_no_service_in_routes(self):
    #    for route_id, usual_stops in self.ROUTE_ID_TO_USUAL_ROUTE.items():
    #        route_response = self._get('systems/testsystem/routes/{}'.format(route_id))
    #        for stop in route_response['stops']:
    #            self.assertFalse(stop['current_service'])

    def test_015_no_feed_updates(self):
        for feed_id in self.FEED_IDS:
            feed_update_response = self._get(
                "systems/testsystem/feeds/{}/updates".format(feed_id)
            )
            expected_num_updates = 0
            if feed_id == "gtfsstatic":
                expected_num_updates = 1
            self.assertEqual(expected_num_updates, len(feed_update_response))

    def test_050_feed_update(self):
        trip_1_stops = {
            "1AS": 300,
            "1BS": 600,
            "1CS": 800,
            "1DS": 900,
            "1ES": 1800,
            "1FS": 2500,
        }

        feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
            0, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
        )

        self._perform_feed_update_stop_test(feed_1)

    def test_051_feed_update(self):
        trip_1_stops = {
            "1AS": 200,
            "1BS": 600,
            "1CS": 800,
            "1DS": 900,
            "1ES": 1800,
            "1FS": 2500,
        }

        feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
            0, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
        )

        self._perform_feed_update_stop_test(feed_1)

    def test_052_feed_update(self):
        trip_1_stops = {
            "1AS": 200,
            "1BS": 600,
            "1CS": 800,
            "1DS": 900,
            "1ES": 1800,
            "1FS": 2500,
            "1GS": 2600,
        }

        feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
            0, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
        )

        self._perform_feed_update_stop_test(feed_1)

    def test_053_feed_update(self):
        trip_1_stops = {"1AS": 200, "1BS": 600, "1CS": 800, "1DS": 900, "1ES": 1800}

        feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
            300, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
        )

        self._perform_feed_update_stop_test(feed_1)

    def test_054_feed_update(self):
        trip_1_stops = {
            "1AS": 300,
            "1BS": 600,
            "1CS": 800,
            "1DS": 900,
            "1ES": 1800,
            "1FS": 2500,
            "1GS": 3000,
        }

        feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
            850, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
        )

        self._perform_feed_update_stop_test(feed_1)

    def test_060_feed_update(self):
        trip_1_stops = {
            "1AS": 300,
            "1BS": 600,
            "1CS": 800,
            "1DS": 900,
            "1ES": 1800,
            "1GS": 2500,
            "1FS": 3000,
        }

        feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
            850, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
        )

        self._perform_feed_update_stop_test(feed_1)

    def test_065_feed_update(self):
        feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(850, [])

        self._perform_feed_update_stop_test(feed_1)

    def _perform_feed_update_stop_test(self, feed_1):
        requests.put("http://localhost:5001", data=feed_1.build_feed())

        self._post("systems/testsystem/feeds/{}".format(self.FEED_IDS[0]))

        all_stop_data = feed_1.stop_data()
        for stop_id, stop_data in all_stop_data.items():

            actual_stop_data = []
            response = self._get("systems/testsystem/stops/{}".format(stop_id))
            for stu in response["stop_time_updates"]:
                actual_stop_data.append(
                    {
                        "trip_id": stu["trip"]["id"],
                        "route_id": stu["trip"]["route"]["id"],
                        "arrival_time": stu["arrival_time"],
                        "departure_time": stu["departure_time"],
                    }
                )

            self.assertListEqual(stop_data, actual_stop_data)

        prev_stop_ids = set(all_stop_data.keys())

        for stop_id in self.STOP_IDS:
            if len(stop_id) <= 2:
                continue
            if stop_id in prev_stop_ids:
                continue
            response = self._get("systems/testsystem/stops/{}".format(stop_id))
            self.assertEqual([], response["stop_time_updates"])

    def test_080_feed_update_trips(self):
        trip_1_stops = {
            "1AS": 300,
            "1BS": 600,
            "1CS": 800,
            "1DS": 900,
            "1ES": 1800,
            "1GS": 2500,
            "1FS": 3000,
        }

        feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
            0, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
        )
        feed_2 = gtfsrealtimegenerator.GtfsRealtimeFeed(
            850, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
        )
        self._perform_feed_update_trip_test([feed_1, feed_2])

    def _perform_feed_update_trip_test(self, feeds):

        for feed in feeds:
            requests.put("http://localhost:5001", data=feed.build_feed())
            self._post("systems/testsystem/feeds/{}".format(self.FEED_IDS[0]))

        all_sss = []
        all_trips = set()
        all_trip_data = []
        for feed in feeds:
            (stop_sequences, trip_data) = feed.trip_data()
            all_sss.append(stop_sequences)
            all_trip_data.append(trip_data)
            all_trips.update(stop_sequences.keys())

        trip_to_expected_data = {trip_id: [] for trip_id in all_trips}
        trip_to_num_passed = {trip_id: 0 for trip_id in all_trips}
        for index, trip_data in enumerate(all_trip_data):
            for trip_id in all_trips:
                if trip_id not in trip_data:
                    trip_to_expected_data[trip_id] = []
                    trip_to_num_passed[trip_id] = 0
                    continue
                current_stop_sequence = all_sss[index][trip_id]
                diff = len(trip_to_expected_data[trip_id]) - current_stop_sequence
                if diff < 0:
                    trip_to_expected_data[trip_id] += [None] * (-diff)
                else:
                    trip_to_expected_data[trip_id] = trip_to_expected_data[trip_id][
                        :current_stop_sequence
                    ]

                trip_to_num_passed[trip_id] = len(trip_to_expected_data[trip_id])

                future_stops = [stop["stop_id"] for stop in trip_data[trip_id]]
                trip_to_expected_data[trip_id] += future_stops

        for trip_id in all_trips:

            expected_stop_list = []
            num_passed = trip_to_num_passed[trip_id]
            for index, stop_data in enumerate(trip_to_expected_data[trip_id]):
                if stop_data is None:
                    continue
                expected_stop_list.append((stop_data, index >= num_passed))

            actual_data = self._get(
                "systems/testsystem/routes/A/trips/{}".format(trip_id)
            )

            actual_stop_list = []
            for stop_data in actual_data["stop_time_updates"]:
                # print(stop_data)
                actual_stop_list.append((stop_data["stop"]["id"], stop_data["future"]))

            print("Actual", actual_stop_list)
            self.assertEqual(expected_stop_list, actual_stop_list)

    # Test service patterns

    # Test routes have no service

    # Test feeds have no feed updates

    # Then run a feed update

    @classmethod
    def _get(cls, endpoint):
        response = requests.get("{}{}".format(cls.TRANSITER_URL, endpoint))
        response.raise_for_status()
        return response.json()

    @classmethod
    def _put(cls, endpoint, *args, **kwargs):
        return requests.put("{}{}".format(cls.TRANSITER_URL, endpoint), *args, **kwargs)

    @classmethod
    def _post(cls, endpoint):
        return requests.post("{}{}".format(cls.TRANSITER_URL, endpoint))


def startup_http_services():
    shutdown_http_services()
    subprocess.call(["python", "--version"])
    print("(Re)building the Transiter DB")
    rebuild_db()
    print("Launching dummy feed server")
    launch_flask_app("feedserver.py")
    print("Launching Transiter server")
    launch_transiter_http_server()
    """
    try:
    """


def shutdown_http_services():
    kill_process_on_port(5000)
    kill_process_on_port(5001)


def rebuild_db():
    subprocess.call(["transiterclt", "rebuild-db", "--yes"])


def launch_transiter_http_server():
    subprocess.Popen(
        ["transiterclt", "launch", "http-debug-server"], stdout=subprocess.DEVNULL
    )
    time.sleep(1.5)


def launch_flask_app(location):
    subprocess.Popen(["python", location], stdout=subprocess.DEVNULL)
    time.sleep(1.5)


def kill_process_on_port(port_number):
    try:
        raw_pids = subprocess.check_output(["lsof", "-t", "-i:{}".format(port_number)])
    except subprocess.CalledProcessError:
        print("No process to kill on port {}".format(port_number))
        return
    pids = raw_pids.decode("utf-8").split()
    for pid in pids:
        subprocess.call(
            ["kill", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )


if __name__ == "__main__":
    suite = IntegrationTest()
    unittest.TextTestRunner().run(suite)
