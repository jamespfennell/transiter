from transiter import models
import datetime

SYSTEM_ONE_PK = 8
SYSTEM_TWO_PK = 9
SYSTEM_ONE_ID = '1'
SYSTEM_TWO_ID = '2'
SYSTEM_THREE_ID = '3'
SYSTEM_THREE_NAME = '4'
SYSTEM_ONE_PACKAGE = '5'
SYSTEM_TWO_PACKAGE = '6'
SYSTEM_THREE_PACKAGE = '7'

system_one = models.System(pk=SYSTEM_ONE_PK, id=SYSTEM_ONE_ID)
system_two = models.System(pk=SYSTEM_TWO_PK, id=SYSTEM_TWO_ID)

ROUTE_ONE_ID = '11'
ROUTE_ONE_PK = 12
ROUTE_TWO_ID = '13'
ROUTE_TWO_PK = 14
ROUTE_THREE_ID = '15'
ROUTE_THREE_PK = 16

route_one = models.Route(pk=ROUTE_ONE_PK, id=ROUTE_ONE_ID, system=system_one)
route_two = models.Route(pk=ROUTE_TWO_PK, id=ROUTE_TWO_ID, system=system_one)
route_three = models.Route(pk=ROUTE_THREE_PK, id=ROUTE_THREE_ID, system=system_one)

TRIP_ONE_ID = '21'
TRIP_ONE_PK = 22
TRIP_TWO_ID = '23'
TRIP_TWO_PK = 24
TRIP_THREE_ID = '25'
TRIP_THREE_PK = 26

trip_one = models.Trip(pk=TRIP_ONE_PK, id=TRIP_ONE_ID, route=route_one, current_status='')
trip_two = models.Trip(pk=TRIP_TWO_PK, id=TRIP_TWO_ID, route=route_one, current_status='')
trip_three = models.Trip(pk=TRIP_THREE_PK, id=TRIP_THREE_ID, route=route_one, current_status='')

STOP_ONE_ID = '41'
STOP_ONE_PK = 42
STOP_TWO_ID = '43'
STOP_TWO_PK = 44
STOP_THREE_ID = '45'
STOP_THREE_PK = 46
STOP_FOUR_ID = '47'
STOP_FOUR_PK = 48
STOP_FIVE_ID = '49'
STOP_FIVE_PK = 50

stop_one = models.Stop(pk=STOP_ONE_PK, id=STOP_ONE_ID, system=system_one, is_station=False)
stop_two = models.Stop(pk=STOP_TWO_PK, id=STOP_TWO_ID, system=system_one, is_station=False)
stop_three = models.Stop(pk=STOP_THREE_PK, id=STOP_THREE_ID, system=system_one, is_station=False)
stop_four = models.Stop(pk=STOP_FOUR_PK, id=STOP_FOUR_ID, system=system_one, is_station=True)
stop_five = models.Stop(pk=STOP_FIVE_PK, id=STOP_FIVE_ID, system=system_one, is_station=True)

STATION_1_PK = 51
STATION_2_PK = 52

station_1 = models.Stop(pk=STATION_1_PK, system=system_one, is_station=True)
station_1.child_stops = [stop_one, stop_two]
station_2 = models.Stop(pk=STATION_2_PK, system=system_one, is_station=True)
station_2.child_stops = [stop_four]

TRIP_ONE_PATH = [stop_one, stop_two, stop_three, stop_four]
TRIP_ONE_TIMES = ['2018-11-02 10:00:00', '2018-11-02 10:01:00',
                  '2018-11-02 10:02:00', '2018-11-02 10:03:00']
TRIP_TWO_PATH = [stop_one, stop_two, stop_four]
TRIP_TWO_TIMES = ['2018-11-02 11:00:00', '2018-11-02 11:01:00', '2018-11-02 11:03:00']
TRIP_THREE_PATH = [stop_one, stop_four]
TRIP_THREE_TIMES = ['2018-11-02 12:00:00', '2018-11-02 12:03:00']

trip_one.stop_events = [
    models.StopTimeUpdate(stop=TRIP_ONE_PATH[i], stop_sequence=i + 1, arrival_time=TRIP_ONE_TIMES[i])
    for i in range(4)
]
trip_two.stop_events = [
    models.StopTimeUpdate(stop=TRIP_TWO_PATH[i], stop_sequence=i + 1, arrival_time=TRIP_TWO_TIMES[i])
    for i in range(3)
]
trip_three.stop_events = [
    models.StopTimeUpdate(stop=TRIP_THREE_PATH[i], stop_sequence=i + 1, arrival_time=TRIP_THREE_TIMES[i])
    for i in range(2)
]

FEED_ONE_ID = '71'
FEED_ONE_PK = 72
FEED_TWO_ID = '73'
FEED_TWO_PK = 74
FEED_3_ID = '75'
FEED_3_PK = 76

feed_one = models.Feed(pk=FEED_ONE_PK, id=FEED_ONE_ID, system=system_one, auto_updater_enabled=True)
feed_two = models.Feed(pk=FEED_TWO_PK, id=FEED_TWO_ID, system=system_one, auto_updater_enabled=False)
feed_3 = models.Feed(pk=FEED_3_PK, id=FEED_3_ID, system=system_two, auto_updater_enabled=True)

feed_1_update_1 = models.FeedUpdate(
    feed_one, status=models.FeedUpdate.Status.SUCCESS,
    last_action_time=datetime.datetime(2011, 1, 1, 1, 0, 0)
)
feed_1_update_2 = models.FeedUpdate(
    feed_one, status=models.FeedUpdate.Status.SUCCESS,
    last_action_time=datetime.datetime(2011, 1, 1, 2, 0, 0)
)
feed_1_update_3 = models.FeedUpdate(
    feed_one, status=models.FeedUpdate.Status.FAILURE,
    last_action_time=datetime.datetime(2011, 1, 1, 3, 0, 0)
)

ALERT_1_PK = 81
ALERT_2_PK = 82
ALERT_3_PK = 83
ALERT_4_PK = 84

alert_1 = models.RouteStatus(pk=ALERT_1_PK, priority=1)
alert_2 = models.RouteStatus(pk=ALERT_2_PK, priority=2)
alert_3 = models.RouteStatus(pk=ALERT_3_PK, priority=2)
alert_4 = models.RouteStatus(pk=ALERT_4_PK, priority=3)

route_one.route_statuses = [alert_1, alert_2, alert_3]
route_two.route_statuses = [alert_1, alert_3, alert_4]

SERVICE_MAP_GROUP_ONE_PK = 101
SERVICE_MAP_GROUP_ONE_ID = '102'
SERVICE_MAP_GROUP_2_PK = 102
SERVICE_MAP_GROUP_2_ID = '103'

service_map_group_1 = models.ServiceMapGroup(
    system=system_one,
    source="realtime",
    use_for_routes_at_stop=True,
    pk=SERVICE_MAP_GROUP_ONE_PK,
    id=SERVICE_MAP_GROUP_ONE_ID)

service_map_group_2 = models.ServiceMapGroup(
    system=system_one,
    source="scheduled",
    use_for_stops_in_route=True,
    pk=SERVICE_MAP_GROUP_2_PK,
    id=SERVICE_MAP_GROUP_2_ID)

SERVICE_PATTERN_ONE_PK = 91
SERVICE_PATTERN_TWO_PK = 92
SERVICE_MAP_2_1_PK = 93

service_map_1_1 = models.ServicePattern(
    group=service_map_group_1,
    route=route_one,
    pk=SERVICE_PATTERN_ONE_PK
)
service_map_1_1.vertices = [
    models.ServicePatternVertex(stop=stop_one),
    models.ServicePatternVertex(stop=stop_two),
]

service_map_1_2 = models.ServicePattern(
    group=service_map_group_1,
    route=route_two,
    pk=SERVICE_PATTERN_TWO_PK
)
service_map_1_2.vertices = [
    models.ServicePatternVertex(stop=stop_two),
    models.ServicePatternVertex(stop=stop_three),
]

service_map_2_1 = models.ServicePattern(
    group=service_map_group_2,
    route=route_two,
    pk=SERVICE_MAP_2_1_PK
)
service_map_2_1.vertices = [
    models.ServicePatternVertex(stop=stop_one),
    models.ServicePatternVertex(stop=stop_two),
]

