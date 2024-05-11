import requests


GTFS_STATIC_DEFAULT_TXTAR = """
-- agency.txt --
agency_name,agency_url,agency_timezone
AgencyName,AgencyURL,AgencyTimezone
-- routes.txt --
route_id,route_type
-- stops.txt --
stop_id
-- stop_times.txt --
trip_id,stop_id,stop_sequence
-- trips.txt --
trip_id,route_id,service_id
"""


GTFS_STATIC_FEED_ID = "gtfs_static"
GTFS_REALTIME_FEED_ID = "gtfs_realtime"


DEFAULT_SYSTEM_CONFIG = """

name: {system_name}

feeds:

  - id: {static_feed_id}
    url: "{static_feed_url}"
    parser: GTFS_STATIC
    requiredForInstall: true

  - id: {realtime_feed_id}
    url: "{realtime_feed_url}"
    parser: GTFS_REALTIME
    schedulingPolicy: PERIODIC
    updatePeriodS: {realtime_periodic_update_period}

"""


class SourceServerClient:
    def __init__(self, base_url, add_finalizer):
        self._created_urls = []
        self._base_url = base_url
        self._add_finalizer = add_finalizer

    def create(self, prefix="", suffix=""):
        response = requests.post(self._base_url)
        response.raise_for_status()
        created_url = response.text + suffix
        self._add_finalizer(self._delete_factory(created_url))
        self._created_urls.append(created_url)
        return created_url

    def put(self, url, content):
        requests.put(self._base_url + "/" + url, data=content).raise_for_status()

    def delete(self, url):
        requests.delete(self._base_url + "/" + url).raise_for_status()

    def _delete_factory(self, url):
        full_url = self._base_url + "/" + url

        def delete():
            requests.delete(full_url)

        return delete
