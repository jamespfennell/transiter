from transiter.services import routeservice

from transiter.taskserver import client

# print(jsonify(systemservice.get('nycsubway')))

"""
#print(jsonify(stopservice.get('L03')))
#print(jsonify(routeservice.get('D')))
if(__name__=='__main__'):
    # print(jsonutil.convert_for_cli(routeservice.get_by_id(None, 'L')))
    #print(jsonutil.convert_for_cli(stopservice.get_by_id(None, 'L03')))

    try:
        systemservice.delete_by_id('nycsubway')
    except exceptions.IdNotFoundError:
        pass

    systemservice.install('nycsubway')

"""


import requests
import json

client.refresh_tasks()


exit()


def compare_responses(rtr_s, transiter_s):
    right = 0
    wrong = 0
    rtr = json.loads(rtr_s)
    trn = json.loads(transiter_s)
    trn_stop_event = {}
    for stop_event in trn["stop_times"]:
        trn_stop_event[stop_event["trip"]["trip_id"]] = stop_event

    for direction in rtr["directions"]:
        for rtr_trip in direction["trips"]:
            if rtr_trip["trip_uid"] not in trn_stop_event:
                print("Trip {} in RTR; not in Transitor".format(rtr_trip["trip_uid"]))
                wrong += 1
                continue

            trn_trip = trn_stop_event[rtr_trip["trip_uid"]]
            del trn_stop_event[rtr_trip["trip_uid"]]
            # print(trip['arrival_time'])
            # print(trn_stop_event[trip['trip_uid']]['arrival_time'])
            if rtr_trip["arrival_time"] == trn_trip["arrival_time"]:
                right += 1
            else:
                if (
                    trn_trip["trip"]["feed_update_time"]
                    != rtr_trip["feed_last_updated"]
                ):
                    continue
                print("Trip {} mismatching details".format(rtr_trip["trip_uid"]))
                print(
                    "   Arrival time: RTR: {}; Transitor: {}".format(
                        rtr_trip["arrival_time"], trn_trip["arrival_time"]
                    )
                )
                # print(jsonutil.convert_for_http(trn_trip))
                # trn_trip['trip']'['feed_update_time']
                wrong += 1

    for trip_id in trn_stop_event.keys():
        print("Trip {} not in RTR; in Transitor".format(trip_id))
    wrong += len(trn_stop_event)
    if right + wrong == 0:
        return 1
    print("Trip matching: {}%".format(right * 100 / (right + wrong)))
    return right / (right + wrong)
    # print('Trips in Transitor not in RTR: {}'.format(len(trn_stop_event)))


"""
from .database.accessobjects import StopDao
stop_dao = StopDao()


stops = stop_dao.list_all_in_system('nycsubway')
stops = reversed(sorted(stops, key = lambda stop: stop.stop_id))
north = None
south = None
lines = []
for stop in stops:
    if len(stop.direction_names) >= 2:
        for direction_name in stop.direction_names:
            if direction_name.track is not None:
                continue
            if direction_name.direction == 'N':
                north = direction_name.name
            else:
                south = direction_name.name
    lines.append((stop.stop_id, north, south))

lines.append(('stop_id', 'north_direction_name', 'south_direction_name'))
lines.reverse()


with open('direction_names.csv', 'w') as f:
    for line in lines:
        f.write('{},{},{}\n'.format(*line))
exit()

"""

stop_ids = set()

routes = routeservice.list_all_in_system("nycsubway")
route_ids = [route["route_id"] for route in routes]
print(route_ids)

# route_ids = ['R'] #, '2', '3', '4', '5', '6', 'L', 'A', 'B', 'C', 'D', 'E', 'F']
for route_id in route_ids:
    route = routeservice.get_in_system_by_id("nycsubway", route_id)
    for stop in route["stops"]:
        stop_ids.add(stop["stop_id"])

print(sorted(stop_ids))

stop_id_to_rtr_response = {}

comparisons = 0
sum_of_proportions = 0


# stop_ids = ['112']*20


for index, stop_id in enumerate(sorted(stop_ids)):

    if index % 10 == 0:
        print("Updating Transitor")
        requests.post("http://localhost:5000/systems/nycsubway/feeds/123456/")
        requests.post("http://localhost:5000/systems/nycsubway/feeds/L/")
        requests.post("http://localhost:5000/systems/nycsubway/feeds/G/")
        requests.post("http://localhost:5000/systems/nycsubway/feeds/ACE/")
        requests.post("http://localhost:5000/systems/nycsubway/feeds/BDFM/")
        requests.post("http://localhost:5000/systems/nycsubway/feeds/NQRW/")
        requests.post("http://localhost:5000/systems/nycsubway/feeds/7/")
        requests.post("http://localhost:5000/systems/nycsubway/feeds/SIR/")
        requests.post("http://localhost:5000/systems/nycsubway/feeds/JZ/")

    print("Retrieving RTR response for stop_id={}".format(stop_id))
    rtr_response = requests.get(
        "https://www.realtimerail.nyc/json/stops/{}.json".format(stop_id)
    ).content
    print("Retrieving Transitor response for stop_id={}".format(stop_id))
    transitor_response = requests.get(
        "http://localhost:5000/systems/nycsubway/stops/{}".format(stop_id)
    ).content
    print("Comparing responses")
    comparisons += 1
    sum_of_proportions += compare_responses(rtr_response, transitor_response)

    # if index == 19:
    #    break

print("Total success: {}%".format(sum_of_proportions * 100 / comparisons))

"""
exit()
print('Updating')
requests.post('http://localhost:5000/systems/nycsubway/feeds/123456/')

stop_id_to_transitor_response = {}

print('Downloading RTR')
rtr_s = requests.get('https://www.realtimerail.nyc/json/stops/635.json').content

print('Reading Transiter')
transiter_s = requests.get('http://localhost:5000/systems/nycsubway/stops/635').content
"""
