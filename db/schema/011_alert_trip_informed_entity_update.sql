ALTER TABLE alert_trip
ADD COLUMN route_pk BIGINT REFERENCES route(pk) ON DELETE SET NULL;

ALTER TABLE alert_trip
ADD COLUMN direction_id boolean;

ALTER TABLE alert_trip
ADD COLUMN start_date timestamp with time zone;

ALTER TABLE alert_trip
ADD COLUMN start_time int;
