ALTER TABLE alert_trip DROP CONSTRAINT fk_alert_trip_trip_pk;
ALTER TABLE alert_trip
    ADD CONSTRAINT fk_alert_trip_pk FOREIGN KEY (trip_pk) REFERENCES trip(pk) ON DELETE SET NULL;
ALTER TABLE alert_trip ALTER COLUMN trip_pk DROP NOT NULL;

ALTER TABLE alert_trip
ADD COLUMN scheduled_trip_pk BIGINT REFERENCES scheduled_trip(pk) ON DELETE SET NULL;

CREATE TABLE alert_route_type (
    alert_pk BIGINT NOT NULL,
    route_type character varying NOT NULL
);

ALTER TABLE alert_route_type
    ADD CONSTRAINT fk_alert_route_type_alert_pk FOREIGN KEY(alert_pk) REFERENCES alert(pk) ON DELETE CASCADE;
