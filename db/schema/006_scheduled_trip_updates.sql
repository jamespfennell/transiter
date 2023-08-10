-- +goose Up

ALTER TABLE scheduled_trip
ALTER COLUMN wheelchair_accessible DROP NOT NULL;

ALTER TABLE scheduled_trip
    ALTER COLUMN wheelchair_accessible DROP DEFAULT,
    ALTER COLUMN wheelchair_accessible TYPE BOOLEAN USING NULL::BOOLEAN,
    ALTER COLUMN wheelchair_accessible SET DEFAULT NULL;

ALTER TABLE scheduled_trip
ALTER COLUMN bikes_allowed DROP NOT NULL;

ALTER TABLE scheduled_trip
    ALTER COLUMN bikes_allowed DROP DEFAULT,
    ALTER COLUMN bikes_allowed TYPE BOOLEAN USING NULL::BOOLEAN,
    ALTER COLUMN bikes_allowed SET DEFAULT NULL;

ALTER TABLE scheduled_trip_frequency DROP COLUMN start_time;
ALTER TABLE scheduled_trip_frequency
ADD COLUMN start_time INT NOT NULL;

ALTER TABLE scheduled_trip_frequency DROP COLUMN end_time;
ALTER TABLE scheduled_trip_frequency
ADD COLUMN end_time INT NOT NULL;

ALTER TABLE scheduled_trip_stop_time DROP COLUMN arrival_time;
ALTER TABLE scheduled_trip_stop_time
ADD COLUMN arrival_time INT;

ALTER TABLE scheduled_trip_stop_time DROP COLUMN departure_time;
ALTER TABLE scheduled_trip_stop_time
ADD COLUMN departure_time INT;

CREATE TABLE scheduled_trip_shape (
    pk BIGSERIAL PRIMARY KEY,
    trip_pk BIGINT NOT NULL REFERENCES scheduled_trip(pk) ON DELETE CASCADE,
    shape JSON NOT NULL
);
