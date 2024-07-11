from . import gtfs_realtime_pb2 as gtfs

def build_gtfs_rt_trip_update_message(
    trip_id,
    route_id,
    current_time,
    stop_id_to_time,
    use_stop_sequences,
    stop_sequence_offset=0,
    feed_id="1",
):
    return gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0", timestamp=current_time),
        entity=[
            gtfs.FeedEntity(
                id=feed_id,
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(
                        trip_id=trip_id, route_id=route_id, direction_id=True
                    ),
                    stop_time_update=[
                        gtfs.TripUpdate.StopTimeUpdate(
                            arrival=gtfs.TripUpdate.StopTimeEvent(time=time),
                            departure=gtfs.TripUpdate.StopTimeEvent(time=time + 15),
                            stop_id=stop_id,
                            stop_sequence=(
                                stop_sequence_offset + stop_sequence if use_stop_sequences else None
                            ),
                        )
                        for stop_sequence, (stop_id, time) in enumerate(
                            stop_id_to_time.items()
                        )
                        if time >= current_time
                    ],
                ),
            )
        ],
    )
