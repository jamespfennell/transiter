import subprocess
import time
import requests
import unittest


class IntegrationTest(unittest.TestCase):

    TRANSITER_URL = 'http://localhost:5000/'

    STOP_IDS = {'1A', '1B', '1C', '1D', '1E', '1F', '1G'}
    ROUTE_IDS = {'A', 'B'}
    FEED_IDS = {'GtfsRealtimeFeed'}
    STOP_ID_TO_USUAL_ROUTES = {
        '1A': ['A'],
        '1B': [],
        '1C': [],
        '1D': ['A'],
        '1E': ['A'],
        '1F': [],
        '1G': [],
    }
    ROUTE_ID_TO_USUAL_ROUTE = {
        'A': ['1A', '1D', '1E'],
        'B': []
    }

    @classmethod
    def setUpClass(cls):
        startup_http_services()

    @classmethod
    def tearDownClass(cls):
        shutdown_http_services()

    def test_000_check_for_no_systems(self):
        response = self._get('systems')
        self.assertEqual(response, [])

    def test_006_install_system_success(self):
        payload = {'package': 'transiter_integrationtestsystem'}
        response = self._put('systems/testsystem', json=payload)
        response.raise_for_status()

    def test_010_count_stops(self):
        system_response = self._get('systems/testsystem')
        stops_count = system_response['stops']['count']
        self.assertEqual(len(self.STOP_IDS), stops_count)

    def test_010_get_stop_ids(self):
        stops_response = self._get('systems/testsystem/stops')
        actual_stop_ids = set([stop['stop_id'] for stop in stops_response])
        self.assertEqual(self.STOP_IDS, actual_stop_ids)

    def test_011_count_feeds(self):
        system_response = self._get('systems/testsystem')
        feeds_count = system_response['feeds']['count']
        self.assertEqual(len(self.FEED_IDS), feeds_count)

    def test_011_get_feed_ids(self):
        feeds_response = self._get('systems/testsystem/feeds')
        actual_feed_ids = set([feed['feed_id'] for feed in feeds_response])
        self.assertEqual(self.FEED_IDS, actual_feed_ids)

    def test_011_count_routes(self):
        system_response = self._get('systems/testsystem')
        routes_count = system_response['routes']['count']
        self.assertEqual(len(self.ROUTE_IDS), routes_count)

    def test_011_get_route_ids(self):
        routes_response = self._get('systems/testsystem/routes')
        actual_route_ids = set([route['route_id'] for route in routes_response])
        self.assertEqual(self.ROUTE_IDS, actual_route_ids)

    def test_012_all_stops_have_no_trips(self):
        for stop_id in self.STOP_IDS:
            stop_response = self._get('systems/testsystem/stops/{}'.format(stop_id))
            self.assertEqual([], stop_response['stop_events'])

    def test_013_stop_usual_routes(self):
        for stop_id, usual_route in self.STOP_ID_TO_USUAL_ROUTES.items():
            stop_response = self._get('systems/testsystem/stops/{}'.format(stop_id))
            self.assertListEqual(usual_route, stop_response['usual_routes'])

    def test_014_route_usual_stops(self):
        for route_id, usual_stops in self.ROUTE_ID_TO_USUAL_ROUTE.items():
            route_response = self._get('systems/testsystem/routes/{}'.format(route_id))
            actual_stops = [stop['stop_id'] for stop in route_response['stops']]
            self.assertListEqual(usual_stops, actual_stops)

    def test_014_no_service_in_routes(self):
        for route_id, usual_stops in self.ROUTE_ID_TO_USUAL_ROUTE.items():
            route_response = self._get('systems/testsystem/routes/{}'.format(route_id))
            for stop in route_response['stops']:
                self.assertFalse(stop['current_service'])

    def test_015_no_feed_updates(self):
        for feed_id in self.FEED_IDS:
            feed_update_response = self._get(
                'systems/testsystem/feeds/{}/updates'.format(feed_id))
            self.assertEqual([], feed_update_response)




    #Test service patterns

    #Test routes have no service

    # Test feeds have no feed updates

    #Then run a feed update

    @classmethod
    def _get(cls, endpoint):
        response =  requests.get('{}{}'.format(cls.TRANSITER_URL, endpoint))
        response.raise_for_status()
        return response.json()

    @classmethod
    def _put(cls, endpoint, json=None):
        return requests.put('{}{}'.format(cls.TRANSITER_URL, endpoint), json=json)


def startup_http_services():
    print('(Re)building the Transiter DB')
    rebuild_db()
    print('Launching dummy feed server')
    launch_flask_app('tests/integrationtest/feedserver.py')
    print('Launching Transiter server')
    launch_flask_app('transiter/endpoints/flaskapp.py')
    """
    try:
    """


def shutdown_http_services():
    kill_process_on_port(5000)
    kill_process_on_port(5001)


def rebuild_db():
    subprocess.call(['python', 'rebuilddb.py'])


def launch_flask_app(location):
    subprocess.Popen(
        ['python', location],
        stdout=subprocess.DEVNULL,
    )
    time.sleep(1.5)


def kill_process_on_port(port_number):
    raw_pids = subprocess.check_output(
        ['lsof', '-t', '-i:{}'.format(port_number)])
    pids = raw_pids.decode('utf-8').split()
    for pid in pids:
        subprocess.call(
            ['kill', pid],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    suite = IntegrationTest()
    unittest.TextTestRunner().run(suite)
