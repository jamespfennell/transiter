-- +goose Up

ALTER TABLE vehicle ALTER COLUMN current_status DROP NOT NULL;
ALTER TABLE vehicle ALTER COLUMN occupancy_status DROP NOT NULL;

ALTER TABLE vehicle
ALTER COLUMN latitude
TYPE numeric(9, 6)
USING latitude::numeric(9, 6);

ALTER TABLE vehicle
ALTER COLUMN longitude
TYPE numeric(9, 6)
USING longitude::numeric(9, 6);

ALTER TABLE vehicle
ALTER COLUMN bearing
TYPE real
USING bearing::real;

ALTER TABLE vehicle
ALTER COLUMN speed
TYPE real
USING speed::real;

ALTER TABLE vehicle
ADD COLUMN occupancy_percentage integer;

ALTER TABLE vehicle DROP CONSTRAINT fk_vehicle_current_stop_pk;
ALTER TABLE vehicle
    ADD CONSTRAINT fk_vehicle_current_stop_pk FOREIGN KEY (current_stop_pk) REFERENCES stop(pk) ON DELETE SET NULL;

ALTER TABLE vehicle DROP CONSTRAINT fk_vehicle_trip_pk;
ALTER TABLE vehicle
    ADD CONSTRAINT fk_vehicle_trip_pk FOREIGN KEY (trip_pk) REFERENCES trip(pk) ON DELETE SET NULL;
