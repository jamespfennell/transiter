INSERT INTO systems (system_id) VALUES (:system_one_id);
INSERT INTO systems (system_id) VALUES (:system_two_id);

INSERT INTO routes (route_id, system_id) VALUES (:route_one_id, :system_one_id);
INSERT INTO routes (route_id, system_id) VALUES (:route_two_id, :system_one_id);
