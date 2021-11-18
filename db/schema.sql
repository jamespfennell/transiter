
CREATE TABLE agency (
    pk SERIAL PRIMARY KEY,
    id character varying NOT NULL,
    system_pk integer NOT NULL,
    source_pk integer NOT NULL,  -- TODO fk
    name character varying NOT NULL,
    url character varying,
    timezone character varying NOT NULL,
    language character varying,
    phone character varying,
    fare_url character varying,
    email character varying,

    CONSTRAINT fk_agency_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE
);

CREATE TABLE feed (
    pk SERIAL PRIMARY KEY,
    id character varying,
    system_pk integer NOT NULL,
    custom_parser character varying,
    url character varying,
    headers character varying,
    auto_update_enabled boolean NOT NULL,
    auto_update_period integer,
    required_for_install boolean DEFAULT false NOT NULL,
    built_in_parser character varying,
    http_timeout double precision,
    parser_options character varying,

    CONSTRAINT fk_feed_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE
);

CREATE TABLE route (
    pk SERIAL PRIMARY KEY,
    id character varying,
    system_pk integer NOT NULL,
    source_pk integer NOT NULL,  -- TODO fk
    color character varying,
    text_color character varying,
    short_name character varying,
    long_name character varying,
    description character varying,
    url character varying,
    sort_order integer,
    type character varying,
    agency_pk integer,  -- TODO fk
    continuous_drop_off character varying(22) DEFAULT 'NOT_ALLOWED'::character varying NOT NULL,
    continuous_pickup character varying(22) DEFAULT 'NOT_ALLOWED'::character varying NOT NULL,

    CONSTRAINT fk_route_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE
);

CREATE TABLE stop (
    pk SERIAL PRIMARY KEY,
    id character varying,
    system_pk integer NOT NULL,
    source_pk integer NOT NULL, -- TODO fk
    parent_stop_pk integer,  -- TODO fk
    name character varying,
    longitude numeric(9,6),
    latitude numeric(9,6),
    url character varying,
    code character varying,
    description character varying,
    platform_code character varying,
    timezone character varying,
    type character varying(16) NOT NULL,
    wheelchair_boarding character varying(14),
    zone_id character varying,

    CONSTRAINT fk_stop_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE
);

CREATE TABLE system (
    pk SERIAL PRIMARY KEY,
    id character varying NOT NULL,
    name character varying NOT NULL,
    timezone character varying,
    auto_update_enabled boolean DEFAULT true NOT NULL,
    status character varying NOT NULL
);

CREATE TABLE transfer (
    pk SERIAL PRIMARY KEY,
    source_pk integer,  -- todo fk
    system_pk integer,
    from_stop_pk integer, -- todo fk
    to_stop_pk integer,  -- todo fk
    type character varying(11) NOT NULL,
    min_transfer_time integer,
    config_source_pk integer, -- todo fk
    distance integer,

    CONSTRAINT transfer_source_constraint CHECK ((NOT ((source_pk IS NULL) AND (config_source_pk IS NULL)))),
    CONSTRAINT fk_transfer_system_pk FOREIGN KEY(system_pk) REFERENCES system(pk) ON DELETE CASCADE
);
