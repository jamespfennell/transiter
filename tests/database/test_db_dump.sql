INSERT INTO systems (system_id) VALUES
    (:system_one_id),
    (:system_two_id);

INSERT INTO routes (id, route_id, system_id) VALUES
    (:route_one_pk,   :route_one_id,   :system_one_id),
    (:route_two_pk,   :route_two_id,   :system_one_id),
    (:route_three_pk, :route_three_id, :system_one_id);

INSERT INTO trips (id, trip_id, route_pri_key, current_status) VALUES
    (:trip_one_pk,   :trip_one_id,   :route_one_pk, ''),
    (:trip_two_pk,   :trip_two_id,   :route_one_pk, ''),
    (:trip_three_pk, :trip_three_id, :route_one_pk, '');

INSERT INTO stops (id, stop_id, system_id) VALUES
    (:stop_one_pk,   :stop_one_id,   :system_one_id),
    (:stop_two_pk,   :stop_two_id,   :system_one_id),
    (:stop_three_pk, :stop_three_id, :system_one_id),
    (:stop_four_pk,  :stop_four_id,  :system_one_id),
    (:stop_five_pk,  :stop_five_id,  :system_one_id);

INSERT INTO stop_events (trip_pri_key, stop_pri_key, sequence_index, arrival_time) VALUES
    (:trip_one_pk,   :stop_one_pk,   1, '2018-11-02 10:00:00'),
    (:trip_one_pk,   :stop_two_pk,   2, '2018-11-02 10:00:10'),
    (:trip_one_pk,   :stop_three_pk, 3, '2018-11-02 10:00:20'),
    (:trip_one_pk,   :stop_four_pk,  4, :earliest_terminal_time),
    (:trip_two_pk,   :stop_one_pk,   1, '2018-11-02 11:00:00'),
    (:trip_two_pk,   :stop_two_pk,   2, '2018-11-02 11:00:10'),
    (:trip_two_pk,   :stop_four_pk,  3, :middle_terminal_time),
    (:trip_three_pk, :stop_one_pk,   1, '2018-11-02 12:00:00'),
    (:trip_three_pk, :stop_four_pk,  2, :latest_terminal_time);

INSERT INTO feeds (id, feed_id, system_id) VALUES
    (:feed_one_pk, :feed_one_id, :system_one_id),
    (:feed_two_pk, :feed_two_id, :system_one_id);

INSERT INTO feed_updates (feed_pri_key, status, last_action_time) VALUES
    (:feed_one_pk, 'SUCCESS_UPDATED',         '2018-11-03 10:00:00'),
    (:feed_one_pk, 'SUCCESS_UPDATED',         :latest_feed_update_time),
    (:feed_one_pk, 'FAILURE_COULD_NOT_PARSE', '2018-11-02 12:00:00');

INSERT INTO route_status (id, message_title) VALUES
    (:route_status_one_pk, :route_status_one_message),
    (:route_status_two_pk, :route_status_two_message);

INSERT INTO route_status_routes (route_status_pri_key, route_pri_key) VALUES
    (:route_status_one_pk, :route_one_pk),
    (:route_status_one_pk, :route_two_pk),
    (:route_status_two_pk, :route_two_pk);
