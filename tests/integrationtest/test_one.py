import subprocess
import time
import requests
import unittest


class IntegrationTest(unittest.TestCase):

    TRANSITER_URL = 'http://localhost:5000/'

    STOP_IDS = {'1A', '1B', '1C', '1D', '1E', '1F', '1G'}

    @classmethod
    def setUpClass(cls):
        startup_http_services()

    @classmethod
    def tearDownClass(cls):
        shutdown_http_services()

    def test_000_check_for_no_systems(self):
        response = self._get('systems')
        self.assertEqual(response, [])

    def test_005_install_system_fail(self):
        pass

    def test_006_install_system_success(self):
        payload = {'package': 'transiter_integrationtestsystem'}
        response = self._put('systems/testsystem', json=payload)
        response.raise_for_status()

    def test_010_count_stops(self):
        system_response = self._get('systems/testsystem')
        stops_count_1 = system_response['stops']['count']
        stops_response = self._get('systems/testsystem/stops')
        stops_count_2 = len(stops_response)
        self.assertEqual(len(self.STOP_IDS), stops_count_1)
        self.assertEqual(len(self.STOP_IDS), stops_count_2)

    def test_010_get_stop_ids(self):
        stops_response = self._get('systems/testsystem/stops')
        actual_stop_ids = set([stop['stop_id'] for stop in stops_response])
        self.assertEqual(self.STOP_IDS, actual_stop_ids)

    def test_011_count_feeds(self):
        pass

    def test_011_get_feed_ids(self):
        pass

    def test_011_count_routes(self):
        pass

    def test_011_get_route_ids(self):
        pass

    def test_012_all_stops_have_no_trips(self):
        pass

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
