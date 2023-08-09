-- +goose Up

/*
The following Rust code was used to generate the changes to the entity tables (the code can be run in the Rust playground).

fn main() {
    for table_name in vec!["agency", "alert", "route", "scheduled_service", "stop", "stop_headsign_rule", "transfer", "trip", "vehicle"] {
        println!["-- {table_name}
ALTER TABLE {table_name} ADD feed_pk BIGSERIAL;
UPDATE {table_name} SET feed_pk = feed_update.feed_pk FROM feed_update WHERE {table_name}.source_pk = feed_update.pk;
ALTER TABLE {table_name} ALTER COLUMN feed_pk SET NOT NULL;
ALTER TABLE {table_name} ADD CONSTRAINT fk_{table_name}_feed_pk FOREIGN KEY (feed_pk) REFERENCES feed (pk) ON DELETE CASCADE;
ALTER TABLE {table_name} DROP COLUMN source_pk;
CREATE INDEX ix_{table_name}_feed_pk ON {table_name} USING btree (feed_pk);
"];
    }
}
*/

-- agency
ALTER TABLE agency ADD feed_pk BIGSERIAL;
UPDATE agency SET feed_pk = feed_update.feed_pk FROM feed_update WHERE agency.source_pk = feed_update.pk;
ALTER TABLE agency ALTER COLUMN feed_pk SET NOT NULL;
ALTER TABLE agency ADD CONSTRAINT fk_agency_feed_pk FOREIGN KEY (feed_pk) REFERENCES feed (pk) ON DELETE CASCADE;
ALTER TABLE agency DROP COLUMN source_pk;
CREATE INDEX ix_agency_feed_pk ON agency USING btree (feed_pk);

-- alert
ALTER TABLE alert ADD feed_pk BIGSERIAL;
UPDATE alert SET feed_pk = feed_update.feed_pk FROM feed_update WHERE alert.source_pk = feed_update.pk;
ALTER TABLE alert ALTER COLUMN feed_pk SET NOT NULL;
ALTER TABLE alert ADD CONSTRAINT fk_alert_feed_pk FOREIGN KEY (feed_pk) REFERENCES feed (pk) ON DELETE CASCADE;
ALTER TABLE alert DROP COLUMN source_pk;
CREATE INDEX ix_alert_feed_pk ON alert USING btree (feed_pk);

-- route
ALTER TABLE route ADD feed_pk BIGSERIAL;
UPDATE route SET feed_pk = feed_update.feed_pk FROM feed_update WHERE route.source_pk = feed_update.pk;
ALTER TABLE route ALTER COLUMN feed_pk SET NOT NULL;
ALTER TABLE route ADD CONSTRAINT fk_route_feed_pk FOREIGN KEY (feed_pk) REFERENCES feed (pk) ON DELETE CASCADE;
ALTER TABLE route DROP COLUMN source_pk;
CREATE INDEX ix_route_feed_pk ON route USING btree (feed_pk);

-- scheduled_service
ALTER TABLE scheduled_service ADD feed_pk BIGSERIAL;
UPDATE scheduled_service SET feed_pk = feed_update.feed_pk FROM feed_update WHERE scheduled_service.source_pk = feed_update.pk;
ALTER TABLE scheduled_service ALTER COLUMN feed_pk SET NOT NULL;
ALTER TABLE scheduled_service ADD CONSTRAINT fk_scheduled_service_feed_pk FOREIGN KEY (feed_pk) REFERENCES feed (pk) ON DELETE CASCADE;
ALTER TABLE scheduled_service DROP COLUMN source_pk;
CREATE INDEX ix_scheduled_service_feed_pk ON scheduled_service USING btree (feed_pk);

-- stop
ALTER TABLE stop ADD feed_pk BIGSERIAL;
UPDATE stop SET feed_pk = feed_update.feed_pk FROM feed_update WHERE stop.source_pk = feed_update.pk;
ALTER TABLE stop ALTER COLUMN feed_pk SET NOT NULL;
ALTER TABLE stop ADD CONSTRAINT fk_stop_feed_pk FOREIGN KEY (feed_pk) REFERENCES feed (pk) ON DELETE CASCADE;
ALTER TABLE stop DROP COLUMN source_pk;
CREATE INDEX ix_stop_feed_pk ON stop USING btree (feed_pk);

-- stop_headsign_rule
ALTER TABLE stop_headsign_rule ADD feed_pk BIGSERIAL;
UPDATE stop_headsign_rule SET feed_pk = feed_update.feed_pk FROM feed_update WHERE stop_headsign_rule.source_pk = feed_update.pk;
ALTER TABLE stop_headsign_rule ALTER COLUMN feed_pk SET NOT NULL;
ALTER TABLE stop_headsign_rule ADD CONSTRAINT fk_stop_headsign_rule_feed_pk FOREIGN KEY (feed_pk) REFERENCES feed (pk) ON DELETE CASCADE;
ALTER TABLE stop_headsign_rule DROP COLUMN source_pk;
CREATE INDEX ix_stop_headsign_rule_feed_pk ON stop_headsign_rule USING btree (feed_pk);

-- transfer
ALTER TABLE transfer ADD feed_pk BIGSERIAL;
UPDATE transfer SET feed_pk = feed_update.feed_pk FROM feed_update WHERE transfer.source_pk = feed_update.pk;
ALTER TABLE transfer ALTER COLUMN feed_pk SET NOT NULL;
ALTER TABLE transfer ADD CONSTRAINT fk_transfer_feed_pk FOREIGN KEY (feed_pk) REFERENCES feed (pk) ON DELETE CASCADE;
ALTER TABLE transfer DROP COLUMN source_pk;
CREATE INDEX ix_transfer_feed_pk ON transfer USING btree (feed_pk);

ALTER TABLE transfer DROP COLUMN config_source_pk;

-- trip
ALTER TABLE trip ADD feed_pk BIGSERIAL;
UPDATE trip SET feed_pk = feed_update.feed_pk FROM feed_update WHERE trip.source_pk = feed_update.pk;
ALTER TABLE trip ALTER COLUMN feed_pk SET NOT NULL;
ALTER TABLE trip ADD CONSTRAINT fk_trip_feed_pk FOREIGN KEY (feed_pk) REFERENCES feed (pk) ON DELETE CASCADE;
ALTER TABLE trip DROP COLUMN source_pk;
CREATE INDEX ix_trip_feed_pk ON trip USING btree (feed_pk);

-- vehicle
ALTER TABLE vehicle ADD feed_pk BIGSERIAL;
UPDATE vehicle SET feed_pk = feed_update.feed_pk FROM feed_update WHERE vehicle.source_pk = feed_update.pk;
ALTER TABLE vehicle ALTER COLUMN feed_pk SET NOT NULL;
ALTER TABLE vehicle ADD CONSTRAINT fk_vehicle_feed_pk FOREIGN KEY (feed_pk) REFERENCES feed (pk) ON DELETE CASCADE;
ALTER TABLE vehicle DROP COLUMN source_pk;
CREATE INDEX ix_vehicle_feed_pk ON vehicle USING btree (feed_pk);

-- Add some columns to the feed table to support functionality that was previously in the updates table
ALTER TABLE feed ADD last_content_hash character varying;
ALTER TABLE feed ADD last_update timestamp with time zone;
ALTER TABLE feed ADD last_successful_update timestamp with time zone;
ALTER TABLE feed ADD last_skipped_update timestamp with time zone;
ALTER TABLE feed ADD last_failed_update timestamp with time zone;

DROP TABLE feed_update;

-- We take the opportunity to clean up the database schema.

-- 1. Delete tables that aren't being used and are unlikely to be used in the future.
DROP TABLE system_update;
DROP TABLE transfers_config_system;
DROP TABLE transfers_config;

-- 2. Fix the trip (route, id) constraint, which was the wrong way around.
ALTER TABLE trip DROP CONSTRAINT trip_id_route_pk_key;
ALTER TABLE trip ADD CONSTRAINT trip_route_pk_id_key UNIQUE(route_pk, id);

-- 3. Create indexes on foreign keys that lack them. There are so many because I thought
-- that foreign keys automatically got indexes.
CREATE INDEX ix_alert_active_period__alert_pk ON alert_active_period USING btree (alert_pk);
CREATE INDEX ix_alert_agency__alert_pk ON alert_agency USING btree (alert_pk);
CREATE INDEX ix_alert_agency__agency_pk ON alert_agency USING btree (agency_pk);
CREATE INDEX ix_alert_route__alert_pk ON alert_route USING btree (alert_pk);
CREATE INDEX ix_alert_route__route_pk ON alert_route USING btree (route_pk);
CREATE INDEX ix_alert_stop__alert_pk ON alert_stop USING btree (alert_pk);
CREATE INDEX ix_alert_stop__stop_pk ON alert_stop USING btree (stop_pk);
CREATE INDEX ix_alert_trip__alert_pk ON alert_trip USING btree (alert_pk);
CREATE INDEX ix_alert_trip__trip_pk ON alert_trip USING btree (trip_pk);
CREATE INDEX ix_route__agency_pk ON route USING btree (agency_pk);
CREATE INDEX ix_scheduled_service_addition__service_pk ON scheduled_service_addition USING btree (service_pk);
CREATE INDEX ix_scheduled_service_removal__service_pk ON scheduled_service_removal USING btree (service_pk);
CREATE INDEX ix_scheduled_trip__service_pk ON scheduled_trip USING btree (service_pk);
CREATE INDEX ix_scheduled_trip_frequency__trip_pk ON scheduled_trip_frequency USING btree (trip_pk);
CREATE INDEX ix_scheduled_trip_stop_time__stop_pk ON scheduled_trip_stop_time USING btree (stop_pk);
CREATE INDEX ix_service_map__config_pk ON service_map USING btree (config_pk);
CREATE INDEX ix_service_map_vertex__stop_pk ON service_map_vertex USING btree (stop_pk);
CREATE INDEX ix_stop__parent_stop_pk ON stop USING btree (parent_stop_pk);
CREATE INDEX ix_transfer__from_stop_pk ON transfer USING btree (from_stop_pk);
CREATE INDEX ix_transfer__to_stop_pk ON transfer USING btree (to_stop_pk);
CREATE INDEX ix_transfer__system_pk ON transfer USING btree (system_pk);
CREATE INDEX ix_vehicle__current_stop_pk ON vehicle USING btree (current_stop_pk);
