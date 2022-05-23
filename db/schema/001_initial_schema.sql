-- +goose Up

CREATE TABLE agency (
    pk BIGSERIAL PRIMARY KEY,
    id character varying NOT NULL,
    system_pk BIGINT NOT NULL,
    source_pk BIGINT NOT NULL,
    name character varying NOT NULL,
    url character varying NOT NULL,
    timezone character varying NOT NULL,
    language character varying,
    phone character varying,
    fare_url character varying,
    email character varying,

    UNIQUE(system_pk, id)
);

CREATE TABLE alert (
    pk BIGSERIAL PRIMARY KEY,
    id character varying NOT NULL,
    source_pk BIGINT NOT NULL,
    system_pk BIGINT NOT NULL,
    cause character varying NOT NULL,
    effect character varying NOT NULL,
    created_at timestamp with time zone,
    sort_order integer,
    updated_at timestamp with time zone,

    UNIQUE(system_pk, id)
);

CREATE TABLE alert_active_period (
    pk BIGSERIAL PRIMARY KEY,
    alert_pk BIGINT NOT NULL,
    starts_at timestamp with time zone,
    ends_at timestamp with time zone
);

CREATE TABLE alert_agency (
    alert_pk BIGINT NOT NULL,
    agency_pk BIGINT NOT NULL
);

CREATE TABLE alert_message (
    pk BIGSERIAL PRIMARY KEY,
    alert_pk BIGINT NOT NULL,
    header character varying NOT NULL,
    description character varying NOT NULL,
    url character varying,
    language character varying
);

CREATE TABLE alert_route (
    alert_pk BIGINT NOT NULL,
    route_pk BIGINT NOT NULL
);

CREATE TABLE alert_stop (
    alert_pk BIGINT NOT NULL,
    stop_pk BIGINT NOT NULL
);

CREATE TABLE alert_trip (
    alert_pk BIGINT NOT NULL,
    trip_pk BIGINT NOT NULL
);

CREATE TABLE stop_headsign_rule (
    pk BIGSERIAL PRIMARY KEY,
    source_pk BIGINT NOT NULL,
    priority integer NOT NULL,
    stop_pk BIGINT NOT NULL,
    track character varying,
    headsign character varying NOT NULL
);

CREATE INDEX ix_stop_headsign_rule_stop_pk_priority ON stop_headsign_rule USING btree (stop_pk, priority);

CREATE TABLE feed (
    pk BIGSERIAL PRIMARY KEY,
    id character varying NOT NULL,
    system_pk BIGINT NOT NULL,
    periodic_update_enabled boolean NOT NULL,
    periodic_update_period integer,
    config character varying NOT NULL,

    UNIQUE(system_pk, id)
);

CREATE TABLE feed_update (
    pk BIGSERIAL PRIMARY KEY,
    feed_pk BIGINT NOT NULL,
    status character varying(16) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,

    -- the following fields are only populated when the update completes
    completed_at timestamp with time zone,
    content_created_at timestamp with time zone,
    content_hash character varying,
    content_length integer,
    result character varying(16),
    result_message character varying,
    total_duration integer
);

CREATE INDEX ix_feed_update_feed_feed_update ON feed_update USING btree (feed_pk, pk);
CREATE INDEX ix_feed_update_status_result_completed_at ON feed_update USING btree (feed_pk, status, result, completed_at);
CREATE INDEX ix_feed_update_success_pk_completed_at ON feed_update USING btree (feed_pk, completed_at) WHERE ((status)::text = 'SUCCESS'::text);

CREATE TABLE route (
    pk BIGSERIAL PRIMARY KEY,
    id character varying NOT NULL,
    system_pk BIGINT NOT NULL,
    source_pk BIGINT NOT NULL,
    color character varying NOT NULL,
    text_color character varying NOT NULL,
    short_name character varying,
    long_name character varying,
    description character varying,
    url character varying,
    sort_order integer,
    type character varying NOT NULL,
    agency_pk BIGINT NOT NULL,
    continuous_drop_off character varying(22) DEFAULT 'NOT_ALLOWED'::character varying NOT NULL,
    continuous_pickup character varying(22) DEFAULT 'NOT_ALLOWED'::character varying NOT NULL,

    UNIQUE(system_pk, id)
);

CREATE TABLE scheduled_service (
    pk BIGSERIAL PRIMARY KEY,
    id character varying NOT NULL,
    system_pk BIGINT NOT NULL,
    source_pk BIGINT NOT NULL,
    monday boolean,
    tuesday boolean,
    wednesday boolean,
    thursday boolean,
    friday boolean,
    saturday boolean,
    sunday boolean,
    end_date date,
    start_date date,

    UNIQUE(system_pk, id)
);

CREATE TABLE scheduled_service_addition (
    pk BIGSERIAL PRIMARY KEY,
    service_pk BIGINT NOT NULL,
    date date NOT NULL
);

CREATE TABLE scheduled_service_removal (
    pk BIGSERIAL PRIMARY KEY,
    service_pk BIGINT NOT NULL,
    date date NOT NULL
);

CREATE TABLE scheduled_trip (
    pk BIGSERIAL PRIMARY KEY,
    id character varying NOT NULL,
    route_pk BIGINT NOT NULL,
    service_pk BIGINT NOT NULL,
    direction_id boolean,
    bikes_allowed character varying(11) DEFAULT 'UNKNOWN'::character varying NOT NULL,
    block_id character varying,
    headsign character varying,
    short_name character varying,
    wheelchair_accessible character varying(14) DEFAULT 'UNKNOWN'::character varying NOT NULL,

    UNIQUE(route_pk, id)
);

CREATE TABLE scheduled_trip_frequency (
    pk BIGSERIAL PRIMARY KEY,
    trip_pk BIGINT NOT NULL,
    start_time time with time zone NOT NULL,
    end_time time with time zone NOT NULL,
    headway integer NOT NULL,
    frequency_based boolean NOT NULL
);

CREATE TABLE scheduled_trip_stop_time (
    pk BIGSERIAL PRIMARY KEY,
    trip_pk BIGINT NOT NULL,
    stop_pk BIGINT NOT NULL,
    arrival_time time without time zone,
    departure_time time without time zone,
    stop_sequence integer NOT NULL,
    continuous_drop_off character varying(22) DEFAULT 'NOT_ALLOWED'::character varying NOT NULL,
    continuous_pickup character varying(22) DEFAULT 'NOT_ALLOWED'::character varying NOT NULL,
    drop_off_type character varying(22) DEFAULT 'ALLOWED'::character varying NOT NULL,
    exact_times boolean DEFAULT false NOT NULL,
    headsign character varying,
    pickup_type character varying(22) DEFAULT 'ALLOWED'::character varying NOT NULL,
    shape_distance_traveled double precision,

    UNIQUE(trip_pk, stop_sequence)
);

CREATE INDEX scheduled_trip_stop_time_trip_pk_departure_time_idx ON scheduled_trip_stop_time USING btree (trip_pk, departure_time);

CREATE TABLE service_map (
    pk BIGSERIAL PRIMARY KEY,
    route_pk BIGINT NOT NULL,
    config_pk BIGINT NOT NULL,

    UNIQUE(route_pk, config_pk)
);

CREATE TABLE service_map_config (
    pk BIGSERIAL PRIMARY KEY,
    id character varying NOT NULL,
    system_pk BIGINT NOT NULL,
    config bytea,
    default_for_routes_at_stop boolean NOT NULL,
    default_for_stops_in_route boolean NOT NULL,

    UNIQUE(system_pk, id)
);

CREATE TABLE service_map_vertex (
    pk BIGSERIAL PRIMARY KEY,
    stop_pk BIGINT NOT NULL,
    map_pk BIGINT NOT NULL,
    "position" integer NOT NULL,

    UNIQUE(map_pk, "position")
);

CREATE TABLE stop (
    pk BIGSERIAL PRIMARY KEY,
    id character varying NOT NULL,
    system_pk BIGINT NOT NULL,
    source_pk BIGINT NOT NULL,
    parent_stop_pk BIGINT,
    name character varying,
    longitude numeric(9,6),
    latitude numeric(9,6),
    url character varying,
    code character varying,
    description character varying,
    platform_code character varying,
    timezone character varying,
    type character varying(16) NOT NULL,
    wheelchair_boarding character varying(14) NOT NULL,
    zone_id character varying,

    UNIQUE(system_pk, id)
);

CREATE INDEX ix_stop_system_pk_latitude ON stop USING btree (system_pk, latitude);
CREATE INDEX ix_stop_system_pk_longitude ON stop USING btree (system_pk, longitude);
CREATE INDEX ix_stop_latitude ON stop USING btree (latitude);
CREATE INDEX ix_stop_longitude ON stop USING btree (longitude);

CREATE TABLE system (
    pk BIGSERIAL PRIMARY KEY,
    id character varying NOT NULL,
    name character varying NOT NULL,
    timezone character varying,
    status character varying NOT NULL,

    UNIQUE(id)
);

CREATE TABLE system_update (
    pk BIGSERIAL PRIMARY KEY,
    system_pk BIGINT NOT NULL,
    status character varying(11) NOT NULL,
    status_message character varying,
    total_duration double precision,
    scheduled_at timestamp with time zone,
    completed_at timestamp with time zone,
    config character varying,
    config_template character varying,
    config_parameters character varying,
    config_source_url character varying,
    transiter_version character varying
);

CREATE INDEX system_update_system_pk_system_update_pk_idx ON system_update USING btree (system_pk, pk);

CREATE TABLE transfer (
    pk BIGSERIAL PRIMARY KEY,
    source_pk BIGINT,
    config_source_pk BIGINT,
    system_pk BIGINT,
    from_stop_pk BIGINT NOT NULL,
    to_stop_pk BIGINT NOT NULL,
    type character varying(30) NOT NULL,
    min_transfer_time integer,
    distance integer,

    CONSTRAINT transfer_source_constraint CHECK ((NOT ((source_pk IS NULL) AND (config_source_pk IS NULL))))
);

CREATE TABLE transfers_config (
    pk BIGSERIAL PRIMARY KEY,
    distance numeric NOT NULL
);

CREATE TABLE transfers_config_system (
    transfers_config_pk BIGINT,
    system_pk BIGINT
);

CREATE TABLE trip (
    pk BIGSERIAL PRIMARY KEY,
    id character varying NOT NULL,
    route_pk BIGINT NOT NULL,
    source_pk BIGINT NOT NULL,
    direction_id boolean,
    started_at timestamp with time zone,

    UNIQUE(id, route_pk)
);

CREATE TABLE trip_stop_time (
    pk BIGSERIAL PRIMARY KEY,
    stop_pk BIGINT NOT NULL,
    trip_pk BIGINT NOT NULL,
    arrival_time timestamp with time zone,
    arrival_delay integer,
    arrival_uncertainty integer,
    departure_time timestamp with time zone,
    departure_delay integer,
    departure_uncertainty integer,
    stop_sequence integer NOT NULL,
    track character varying,
    past boolean NOT NULL,

    UNIQUE(trip_pk, stop_sequence)
);

CREATE INDEX trip_stop_time_stop_pk_arrival_time_idx ON trip_stop_time USING btree (stop_pk, arrival_time);

CREATE TABLE vehicle (
    pk BIGSERIAL PRIMARY KEY,
    id character varying,
    source_pk BIGINT NOT NULL,
    system_pk BIGINT NOT NULL,
    trip_pk BIGINT,
    label character varying,
    license_plate character varying,
    current_status character varying(13) NOT NULL,
    latitude double precision,
    longitude double precision,
    bearing double precision,
    odometer double precision,
    speed double precision,
    congestion_level character varying(24) NOT NULL,
    updated_at timestamp with time zone,
    current_stop_pk BIGINT,
    current_stop_sequence integer,
    occupancy_status character varying(26) NOT NULL,

    UNIQUE(trip_pk),
    UNIQUE(system_pk, id)
);

ALTER TABLE agency
    ADD CONSTRAINT fk_agency_source_pk FOREIGN KEY (source_pk) REFERENCES feed_update(pk) ON DELETE CASCADE;
ALTER TABLE agency
    ADD CONSTRAINT fk_agency_system_pk FOREIGN KEY (system_pk) REFERENCES system(pk) ON DELETE CASCADE;

ALTER TABLE alert
    ADD CONSTRAINT fk_alert_source_pk FOREIGN KEY (source_pk) REFERENCES feed_update(pk) ON DELETE CASCADE;
ALTER TABLE alert
    ADD CONSTRAINT fk_alert_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE;
    
ALTER TABLE alert_active_period
    ADD CONSTRAINT fk_alert_active_period_alert_pk FOREIGN KEY(alert_pk) REFERENCES alert(pk) ON DELETE CASCADE;

ALTER TABLE alert_agency
    ADD CONSTRAINT fk_alert_agency_alert_pk FOREIGN KEY(alert_pk) REFERENCES alert(pk) ON DELETE CASCADE;
ALTER TABLE alert_agency
    ADD CONSTRAINT fk_alert_agency_agency_pk FOREIGN KEY(agency_pk) REFERENCES agency(pk) ON DELETE CASCADE;

ALTER TABLE alert_message
    ADD CONSTRAINT fk_alert_message_alert_pk FOREIGN KEY(alert_pk) REFERENCES alert(pk) ON DELETE CASCADE;

ALTER TABLE alert_route
    ADD CONSTRAINT fk_alert_route_alert_pk FOREIGN KEY(alert_pk) REFERENCES alert(pk) ON DELETE CASCADE;
ALTER TABLE alert_route
    ADD CONSTRAINT fk_alert_route_route_pk FOREIGN KEY(route_pk) REFERENCES route(pk) ON DELETE CASCADE;

ALTER TABLE alert_stop
    ADD CONSTRAINT fk_alert_stop_alert_pk FOREIGN KEY(alert_pk) REFERENCES alert(pk) ON DELETE CASCADE;
ALTER TABLE alert_stop
    ADD CONSTRAINT fk_alert_stop_stop_pk FOREIGN KEY(stop_pk) REFERENCES stop(pk) ON DELETE CASCADE;

ALTER TABLE alert_trip
    ADD CONSTRAINT fk_alert_trip_alert_pk FOREIGN KEY(alert_pk) REFERENCES alert(pk) ON DELETE CASCADE;
ALTER TABLE alert_trip
    ADD CONSTRAINT fk_alert_trip_trip_pk FOREIGN KEY(trip_pk) REFERENCES trip(pk) ON DELETE CASCADE;

ALTER TABLE stop_headsign_rule
    ADD CONSTRAINT fk_stop_headsign_rule_source_pk FOREIGN KEY (source_pk) REFERENCES feed_update(pk) ON DELETE CASCADE;
ALTER TABLE stop_headsign_rule
    ADD CONSTRAINT fk_stop_headsign_rule_stop_pk FOREIGN KEY(stop_pk) REFERENCES stop(pk) ON DELETE CASCADE;

ALTER TABLE feed
    ADD CONSTRAINT fk_feed_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE;

ALTER TABLE feed_update
    ADD CONSTRAINT fk_feed_update_feed_pk FOREIGN KEY(feed_pk) REFERENCES feed(pk) ON DELETE CASCADE;

ALTER TABLE route
    ADD CONSTRAINT fk_route_agency_pk FOREIGN KEY (agency_pk) REFERENCES agency(pk);
ALTER TABLE route
    ADD CONSTRAINT fk_route_source_pk FOREIGN KEY (source_pk) REFERENCES feed_update(pk) ON DELETE CASCADE;
ALTER TABLE route
    ADD CONSTRAINT fk_route_system_pk FOREIGN KEY (system_pk) REFERENCES system(pk) ON DELETE CASCADE;

ALTER TABLE scheduled_service
    ADD CONSTRAINT fk_scheduled_service_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE;
ALTER TABLE scheduled_service
    ADD CONSTRAINT fk_scheduled_service_source_pk FOREIGN KEY(source_pk) REFERENCES feed_update(pk) ON DELETE CASCADE;

ALTER TABLE scheduled_service_addition
    ADD CONSTRAINT fk_scheduled_service_addition_service_pk FOREIGN KEY(service_pk) REFERENCES scheduled_service(pk) ON DELETE CASCADE;

ALTER TABLE scheduled_service_removal
    ADD CONSTRAINT fk_scheduled_service_removal_service_pk FOREIGN KEY(service_pk) REFERENCES scheduled_service(pk) ON DELETE CASCADE;

ALTER TABLE scheduled_trip
    ADD CONSTRAINT fk_scheduled_trip_route_pk FOREIGN KEY(route_pk) REFERENCES route(pk) ON DELETE CASCADE;
ALTER TABLE scheduled_trip
    ADD CONSTRAINT fk_scheduled_trip_service_pk FOREIGN KEY(service_pk) REFERENCES scheduled_service(pk) ON DELETE CASCADE;

ALTER TABLE scheduled_trip_frequency
    ADD CONSTRAINT fk_scheduled_trip_frequency_trip_pk FOREIGN KEY(trip_pk) REFERENCES scheduled_trip(pk) ON DELETE CASCADE;

ALTER TABLE scheduled_trip_stop_time
    ADD CONSTRAINT fk_scheduled_trip_stop_time_trip_pk FOREIGN KEY(trip_pk) REFERENCES scheduled_trip(pk) ON DELETE CASCADE;
ALTER TABLE scheduled_trip_stop_time
    ADD CONSTRAINT fk_scheduled_trip_stop_time_stop_pk FOREIGN KEY(stop_pk) REFERENCES stop(pk) ON DELETE CASCADE;

ALTER TABLE service_map
    ADD CONSTRAINT fk_service_map_route_pk FOREIGN KEY(route_pk) REFERENCES route(pk) ON DELETE CASCADE;
ALTER TABLE service_map
    ADD CONSTRAINT fk_service_map_config_pk FOREIGN KEY(config_pk) REFERENCES service_map_config(pk) ON DELETE CASCADE;

ALTER TABLE service_map_config
    ADD CONSTRAINT fk_service_map_config_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE;

ALTER TABLE service_map_vertex
    ADD CONSTRAINT fk_service_map_vertex_stop_pk FOREIGN KEY(stop_pk) REFERENCES stop(pk) ON DELETE CASCADE;
ALTER TABLE service_map_vertex
    ADD CONSTRAINT fk_service_map_vertex_map_pk FOREIGN KEY(map_pk) REFERENCES service_map(pk) ON DELETE CASCADE;

ALTER TABLE stop
    ADD CONSTRAINT fk_stop_parent_stop_pk FOREIGN KEY (parent_stop_pk) REFERENCES stop(pk);
ALTER TABLE stop
    ADD CONSTRAINT fk_stop_source_pk FOREIGN KEY (source_pk) REFERENCES feed_update(pk) ON DELETE CASCADE;
ALTER TABLE stop
    ADD CONSTRAINT fk_stop_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE;

ALTER TABLE system_update
    ADD CONSTRAINT fk_system_update_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE;

ALTER TABLE transfer
    ADD CONSTRAINT fk_transfer_source_pk FOREIGN KEY (source_pk) REFERENCES feed_update(pk) ON DELETE CASCADE;
ALTER TABLE transfer
    ADD CONSTRAINT fk_transfer_config_source_pk FOREIGN KEY (config_source_pk) REFERENCES transfers_config(pk) ON DELETE CASCADE;
ALTER TABLE transfer
    ADD CONSTRAINT fk_transfer_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE;
ALTER TABLE transfer
    ADD CONSTRAINT fk_transfer_from_stop_pk FOREIGN KEY (from_stop_pk) REFERENCES stop(pk) ON DELETE CASCADE;
ALTER TABLE transfer
    ADD CONSTRAINT fk_transfer_to_stop_pk FOREIGN KEY (to_stop_pk) REFERENCES stop(pk) ON DELETE CASCADE;

ALTER TABLE transfers_config_system
    ADD CONSTRAINT fk_transfers_config_system_transfers_config_pk FOREIGN KEY(transfers_config_pk) REFERENCES transfers_config(pk) ON DELETE CASCADE;
ALTER TABLE transfers_config_system
    ADD CONSTRAINT fk_transfers_config_system_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE;

ALTER TABLE trip
    ADD CONSTRAINT fk_trip_route_pk FOREIGN KEY (route_pk) REFERENCES route(pk) ON DELETE CASCADE;
ALTER TABLE trip 
    ADD CONSTRAINT fk_trip_source_pk FOREIGN KEY (source_pk) REFERENCES feed_update(pk) ON DELETE CASCADE;

ALTER TABLE trip_stop_time
    ADD CONSTRAINT fk_trip_stop_time_stop_pk FOREIGN KEY (stop_pk) REFERENCES stop(pk) ON DELETE CASCADE;
ALTER TABLE trip_stop_time
    ADD CONSTRAINT fk_trip_stop_time_trip_pk FOREIGN KEY (trip_pk) REFERENCES trip(pk) ON DELETE CASCADE;

ALTER TABLE vehicle
    ADD CONSTRAINT fk_vehicle_current_stop_pk FOREIGN KEY (current_stop_pk) REFERENCES stop(pk);
ALTER TABLE vehicle
    ADD CONSTRAINT fk_vehicle_source_pk FOREIGN KEY (source_pk) REFERENCES feed_update(pk) ON DELETE CASCADE;
ALTER TABLE vehicle
    ADD CONSTRAINT fk_vehicle_system_pk FOREIGN KEY (system_pk) REFERENCES system(pk) ON DELETE CASCADE;
ALTER TABLE vehicle
    ADD CONSTRAINT fk_vehicle_trip_pk FOREIGN KEY (trip_pk) REFERENCES trip(pk);
