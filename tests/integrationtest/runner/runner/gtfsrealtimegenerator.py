from google.transit import gtfs_realtime_pb2


class FeedTrip:
    def __init__(self, trip_id, route_id, stops_dict, base_time):
        self.trip_id = trip_id
        self.route_id = route_id
        self.stops_dict = {key: value + base_time for key, value in stops_dict.items()}


class GtfsRealtimeFeed:
    def __init__(self, feed_time, feed_trips):

        self.feed_time = feed_time
        self.feed_trips = feed_trips

    def build_feed(self):

        feed_message = gtfs_realtime_pb2.FeedMessage()

        header = feed_message.header
        header.gtfs_realtime_version = "2.0"
        header.timestamp = self.feed_time
        header.incrementality = 0
        # feed_header.incrementality = gtfs_realtime_pb2..Incrementality.FULL_DATASET

        for index, trip in enumerate(self.feed_trips):
            trip_entity = feed_message.entity.add()
            trip_entity.id = str(index)

            trip_update = trip_entity.trip_update

            trip_descr = trip_update.trip
            trip_descr.trip_id = trip.trip_id
            trip_descr.route_id = trip.route_id

            num_ignored_stops = 0
            for stop_id, time in trip.stops_dict.items():
                if time < self.feed_time:
                    num_ignored_stops += 1
                    continue

                stu = trip_update.stop_time_update.add()
                stu.stop_id = stop_id
                stu.arrival.time = time
                stu.departure.time = time + 15

            vehicle_position = trip_entity.vehicle
            trip_descr = vehicle_position.trip
            trip_descr.trip_id = trip.trip_id
            trip_descr.route_id = trip.route_id
            vehicle_position.current_stop_sequence = num_ignored_stops
            trip.current_stop_sequence = num_ignored_stops
        # gtfs_realtime_pb2._FEEDHEADER_INCREMENTALITY
        # print(feed_message)
        return feed_message.SerializeToString()

    def stop_data(self):

        stop_data = {}
        for trip in self.feed_trips:
            for stop_id, time in trip.stops_dict.items():
                if time < self.feed_time:
                    continue
                stop_data.setdefault(stop_id, [])
                stop_data[stop_id].append(
                    {
                        "trip_id": trip.trip_id,
                        "route_id": trip.route_id,
                        "arrival_time": time,
                        "departure_time": time + 15,
                    }
                )
        return stop_data

    def trip_data(self):

        trip_data = {}
        stop_sequences = {}
        for trip in self.feed_trips:
            stop_sequences[trip.trip_id] = trip.current_stop_sequence
            for stop_id, time in trip.stops_dict.items():
                if time < self.feed_time:
                    continue
                trip_data.setdefault(trip.trip_id, [])
                trip_data[trip.trip_id].append(
                    {
                        "stop_id": stop_id,
                        "route_id": trip.route_id,
                        "arrival_time": time,
                        "departure_time": time + 15,
                    }
                )
        return (stop_sequences, trip_data)


"""

trip_1_stops = {
    '1AS': 0,
    '1BS': 300
}
trip = FeedTrip("trip_1", 'A', trip_1_stops, 0)

feed = GtfsRealtimeFeed(00, [trip]).build_feed()

import requests

#requests.put('http://localhost:5001', data=feed)
#print(requests.get('http://localhost:5001').content)



gtfs = gtfs_realtime_pb2.FeedMessage()
gtfs.ParseFromString(feed)
print(gtfs)



"""
