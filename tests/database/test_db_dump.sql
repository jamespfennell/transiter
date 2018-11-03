INSERT INTO systems (system_id) VALUES (:system_one_id);
INSERT INTO systems (system_id) VALUES (:system_two_id);

INSERT INTO routes (id, route_id, system_id) VALUES (:route_one_pk, :route_one_id, :system_one_id);
INSERT INTO routes (id, route_id, system_id) VALUES (:route_two_pk, :route_two_id, :system_one_id);

INSERT INTO trips (trip_id, route_pri_key) VALUES (:trip_one_id, :route_one_pk);
INSERT INTO trips (trip_id, route_pri_key) VALUES (:trip_two_id, :route_one_pk);
