



CREATE TABLE public.alert (
    pk integer NOT NULL,
    id character varying,
    source_pk integer NOT NULL,
    system_pk integer,
    cause character varying NOT NULL,
    effect character varying NOT NULL,
    created_at timestamp with time zone,
    sort_order integer,
    updated_at timestamp with time zone
);


CREATE TABLE public.alert_active_period (
    pk integer NOT NULL,
    alert_pk integer NOT NULL,
    starts_at timestamp with time zone,
    ends_at timestamp with time zone
);



CREATE TABLE public.alert_agency (
    alert_pk integer,
    agency_pk integer
);

CREATE TABLE public.alert_message (
    pk integer NOT NULL,
    alert_pk integer NOT NULL,
    header character varying NOT NULL,
    description character varying NOT NULL,
    url character varying,
    language character varying
);


CREATE TABLE public.alert_route (
    alert_pk integer,
    route_pk integer
);

CREATE TABLE public.alert_stop (
    alert_pk integer,
    stop_pk integer
);

CREATE TABLE public.alert_trip (
    alert_pk integer,
    trip_pk integer
);

CREATE TABLE public.direction_name_rule (
    pk integer NOT NULL,
    id character varying,
    stop_pk integer,
    source_pk integer NOT NULL,
    priority integer,
    direction_id boolean,
    track character varying,
    name character varying
);


CREATE TABLE public.feed_update (
    pk integer NOT NULL,
    feed_pk integer,
    content_length integer,
    completed_at timestamp with time zone,
    content_created_at timestamp with time zone,
    content_hash character varying,
    download_duration double precision,
    result character varying(16),
    num_parsed_entities integer,
    num_added_entities integer,
    num_updated_entities integer,
    num_deleted_entities integer,
    result_message character varying,
    scheduled_at timestamp with time zone,
    total_duration double precision,
    update_type character varying NOT NULL,
    status character varying
);


CREATE TABLE public.scheduled_service (
    pk integer NOT NULL,
    id character varying NOT NULL,
    system_pk integer,
    source_pk integer NOT NULL,
    monday boolean,
    tuesday boolean,
    wednesday boolean,
    thursday boolean,
    friday boolean,
    saturday boolean,
    sunday boolean,
    end_date date,
    start_date date
);


CREATE TABLE public.scheduled_service_addition (
    pk integer NOT NULL,
    service_pk integer,
    date date NOT NULL
);


CREATE TABLE public.scheduled_service_removal (
    pk integer NOT NULL,
    service_pk integer,
    date date NOT NULL
);
CREATE TABLE public.scheduled_trip (
    pk integer NOT NULL,
    id character varying NOT NULL,
    route_pk integer NOT NULL,
    service_pk integer NOT NULL,
    direction_id boolean,
    bikes_allowed character varying(11) DEFAULT 'UNKNOWN'::character varying NOT NULL,
    block_id character varying,
    headsign character varying,
    short_name character varying,
    wheelchair_accessible character varying(14) DEFAULT 'UNKNOWN'::character varying NOT NULL
);


CREATE TABLE public.scheduled_trip_frequency (
    pk integer NOT NULL,
    trip_pk integer NOT NULL,
    start_time time with time zone NOT NULL,
    end_time time with time zone NOT NULL,
    headway integer NOT NULL,
    frequency_based boolean NOT NULL
);


CREATE TABLE public.scheduled_trip_stop_time (
    pk integer NOT NULL,
    trip_pk integer NOT NULL,
    stop_pk integer NOT NULL,
    arrival_time time without time zone,
    departure_time time without time zone,
    stop_sequence integer NOT NULL,
    continuous_drop_off character varying(22) DEFAULT 'NOT_ALLOWED'::character varying NOT NULL,
    continuous_pickup character varying(22) DEFAULT 'NOT_ALLOWED'::character varying NOT NULL,
    drop_off_type character varying(22) DEFAULT 'ALLOWED'::character varying NOT NULL,
    exact_times boolean DEFAULT false NOT NULL,
    headsign character varying,
    pickup_type character varying(22) DEFAULT 'ALLOWED'::character varying NOT NULL,
    shape_distance_traveled double precision
);


CREATE TABLE public.service_map (
    pk integer NOT NULL,
    route_pk integer NOT NULL,
    group_pk integer NOT NULL
);


ALTER TABLE public.service_map OWNER TO transiter;

--
-- Name: service_map_group; Type: TABLE; Schema: public; Owner: transiter
--

CREATE TABLE public.service_map_group (
    pk integer NOT NULL,
    id character varying NOT NULL,
    system_pk integer NOT NULL,
    conditions character varying,
    threshold double precision NOT NULL,
    use_for_routes_at_stop boolean NOT NULL,
    use_for_stops_in_route boolean NOT NULL,
    source character varying NOT NULL
);


ALTER TABLE public.service_map_group OWNER TO transiter;

--
-- Name: service_map_group_pk_seq; Type: SEQUENCE; Schema: public; Owner: transiter
--

CREATE SEQUENCE public.service_map_group_pk_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.service_map_group_pk_seq OWNER TO transiter;

--
-- Name: service_map_group_pk_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: transiter
--

ALTER SEQUENCE public.service_map_group_pk_seq OWNED BY public.service_map_group.pk;


--
-- Name: service_map_pk_seq; Type: SEQUENCE; Schema: public; Owner: transiter
--

CREATE SEQUENCE public.service_map_pk_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.service_map_pk_seq OWNER TO transiter;

--
-- Name: service_map_pk_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: transiter
--

ALTER SEQUENCE public.service_map_pk_seq OWNED BY public.service_map.pk;


--
-- Name: service_map_vertex; Type: TABLE; Schema: public; Owner: transiter
--

CREATE TABLE public.service_map_vertex (
    pk integer NOT NULL,
    stop_pk integer,
    map_pk integer,
    "position" integer
);


ALTER TABLE public.service_map_vertex OWNER TO transiter;

--
-- Name: service_map_vertex_pk_seq; Type: SEQUENCE; Schema: public; Owner: transiter
--

CREATE SEQUENCE public.service_map_vertex_pk_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.service_map_vertex_pk_seq OWNER TO transiter;

--
-- Name: service_map_vertex_pk_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: transiter
--

ALTER SEQUENCE public.service_map_vertex_pk_seq OWNED BY public.service_map_vertex.pk;


--
-- Name: stop; Type: TABLE; Schema: public; Owner: transiter
--




ALTER TABLE public.stop OWNER TO transiter;

--
-- Name: stop_pk_seq; Type: SEQUENCE; Schema: public; Owner: transiter
--

CREATE SEQUENCE public.stop_pk_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stop_pk_seq OWNER TO transiter;

--
-- Name: stop_pk_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: transiter
--

ALTER SEQUENCE public.stop_pk_seq OWNED BY public.stop.pk;


--
-- Name: system; Type: TABLE; Schema: public; Owner: transiter
--


--
-- Name: system_update; Type: TABLE; Schema: public; Owner: transiter
--

CREATE TABLE public.system_update (
    pk integer NOT NULL,
    system_pk integer,
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


ALTER TABLE public.system_update OWNER TO transiter;

--
-- Name: system_update_pk_seq; Type: SEQUENCE; Schema: public; Owner: transiter
--

CREATE SEQUENCE public.system_update_pk_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.system_update_pk_seq OWNER TO transiter;

--
-- Name: system_update_pk_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: transiter
--

ALTER SEQUENCE public.system_update_pk_seq OWNED BY public.system_update.pk;


--
-- Name: transfer; Type: TABLE; Schema: public; Owner: transiter
--



ALTER TABLE public.transfer OWNER TO transiter;

--
-- Name: transfer_pk_seq; Type: SEQUENCE; Schema: public; Owner: transiter
--

CREATE SEQUENCE public.transfer_pk_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.transfer_pk_seq OWNER TO transiter;

--
-- Name: transfer_pk_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: transiter
--

ALTER SEQUENCE public.transfer_pk_seq OWNED BY public.transfer.pk;


--
-- Name: transfers_config; Type: TABLE; Schema: public; Owner: transiter
--

CREATE TABLE public.transfers_config (
    pk integer NOT NULL,
    distance numeric NOT NULL
);


ALTER TABLE public.transfers_config OWNER TO transiter;

--
-- Name: transfers_config_pk_seq; Type: SEQUENCE; Schema: public; Owner: transiter
--

CREATE SEQUENCE public.transfers_config_pk_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.transfers_config_pk_seq OWNER TO transiter;

--
-- Name: transfers_config_pk_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: transiter
--

ALTER SEQUENCE public.transfers_config_pk_seq OWNED BY public.transfers_config.pk;


--
-- Name: transfers_config_system; Type: TABLE; Schema: public; Owner: transiter
--

CREATE TABLE public.transfers_config_system (
    transfers_config_pk integer,
    system_pk integer
);


ALTER TABLE public.transfers_config_system OWNER TO transiter;

--
-- Name: trip; Type: TABLE; Schema: public; Owner: transiter
--

CREATE TABLE public.trip (
    pk integer NOT NULL,
    id character varying,
    route_pk integer NOT NULL,
    source_pk integer NOT NULL,
    direction_id boolean,
    delay integer,
    started_at timestamp with time zone,
    updated_at timestamp with time zone,
    current_stop_sequence integer
);


ALTER TABLE public.trip OWNER TO transiter;

--
-- Name: trip_pk_seq; Type: SEQUENCE; Schema: public; Owner: transiter
--

CREATE SEQUENCE public.trip_pk_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.trip_pk_seq OWNER TO transiter;

--
-- Name: trip_pk_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: transiter
--

ALTER SEQUENCE public.trip_pk_seq OWNED BY public.trip.pk;


--
-- Name: trip_stop_time; Type: TABLE; Schema: public; Owner: transiter
--

CREATE TABLE public.trip_stop_time (
    pk integer NOT NULL,
    stop_pk integer NOT NULL,
    trip_pk integer NOT NULL,
    arrival_time timestamp with time zone,
    arrival_delay integer,
    arrival_uncertainty integer,
    departure_time timestamp with time zone,
    departure_delay integer,
    departure_uncertainty integer,
    stop_sequence integer NOT NULL,
    track character varying
);


ALTER TABLE public.trip_stop_time OWNER TO transiter;

--
-- Name: trip_stop_time_pk_seq; Type: SEQUENCE; Schema: public; Owner: transiter
--

CREATE SEQUENCE public.trip_stop_time_pk_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.trip_stop_time_pk_seq OWNER TO transiter;

--
-- Name: trip_stop_time_pk_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: transiter
--

ALTER SEQUENCE public.trip_stop_time_pk_seq OWNED BY public.trip_stop_time.pk;


--
-- Name: vehicle; Type: TABLE; Schema: public; Owner: transiter
--

CREATE TABLE public.vehicle (
    pk integer NOT NULL,
    id character varying,
    source_pk integer NOT NULL,
    system_pk integer NOT NULL,
    trip_pk integer,
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
    current_stop_pk integer,
    current_stop_sequence integer,
    occupancy_status character varying(26) NOT NULL
);


ALTER TABLE public.vehicle OWNER TO transiter;

--
-- Name: vehicle_pk_seq; Type: SEQUENCE; Schema: public; Owner: transiter
--

CREATE SEQUENCE public.vehicle_pk_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;




--
-- Name: agency agency_system_pk_id_key; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.agency
    ADD CONSTRAINT agency_system_pk_id_key UNIQUE (system_pk, id);



ALTER TABLE ONLY public.alert
    ADD CONSTRAINT alert_system_pk_id_key UNIQUE (system_pk, id);


--
-- Name: direction_name_rule direction_name_rule_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.direction_name_rule
    ADD CONSTRAINT direction_name_rule_pkey PRIMARY KEY (pk);


--
-- Name: direction_name_rule direction_name_rule_source_pk_id_key; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.direction_name_rule
    ADD CONSTRAINT direction_name_rule_source_pk_id_key UNIQUE (source_pk, id);


--
-- Name: feed feed_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.feed
    ADD CONSTRAINT feed_pkey PRIMARY KEY (pk);


--
-- Name: feed feed_system_pk_id_key; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.feed
    ADD CONSTRAINT feed_system_pk_id_key UNIQUE (system_pk, id);


--
-- Name: feed_update feed_update_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.feed_update
    ADD CONSTRAINT feed_update_pkey PRIMARY KEY (pk);


--
-- Name: route route_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.route
    ADD CONSTRAINT route_pkey PRIMARY KEY (pk);


--
-- Name: route route_system_pk_id_key; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.route
    ADD CONSTRAINT route_system_pk_id_key UNIQUE (system_pk, id);


--
-- Name: scheduled_service_addition scheduled_service_addition_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_service_addition
    ADD CONSTRAINT scheduled_service_addition_pkey PRIMARY KEY (pk);


--
-- Name: scheduled_service scheduled_service_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_service
    ADD CONSTRAINT scheduled_service_pkey PRIMARY KEY (pk);


--
-- Name: scheduled_service_removal scheduled_service_removal_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_service_removal
    ADD CONSTRAINT scheduled_service_removal_pkey PRIMARY KEY (pk);


--
-- Name: scheduled_service scheduled_service_system_pk_id_key; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_service
    ADD CONSTRAINT scheduled_service_system_pk_id_key UNIQUE (system_pk, id);


--
-- Name: scheduled_trip_frequency scheduled_trip_frequency_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_trip_frequency
    ADD CONSTRAINT scheduled_trip_frequency_pkey PRIMARY KEY (pk);


--
-- Name: scheduled_trip scheduled_trip_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_trip
    ADD CONSTRAINT scheduled_trip_pkey PRIMARY KEY (pk);


--
-- Name: scheduled_trip_stop_time scheduled_trip_stop_time_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_trip_stop_time
    ADD CONSTRAINT scheduled_trip_stop_time_pkey PRIMARY KEY (pk);


--
-- Name: scheduled_trip_stop_time scheduled_trip_stop_time_trip_pk_stop_sequence_key; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_trip_stop_time
    ADD CONSTRAINT scheduled_trip_stop_time_trip_pk_stop_sequence_key UNIQUE (trip_pk, stop_sequence);


--
-- Name: service_map_group service_map_group_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.service_map_group
    ADD CONSTRAINT service_map_group_pkey PRIMARY KEY (pk);


--
-- Name: service_map service_map_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.service_map
    ADD CONSTRAINT service_map_pkey PRIMARY KEY (pk);


--
-- Name: service_map service_map_route_pk_group_pk_key; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.service_map
    ADD CONSTRAINT service_map_route_pk_group_pk_key UNIQUE (route_pk, group_pk);


--
-- Name: service_map_vertex service_map_vertex_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.service_map_vertex
    ADD CONSTRAINT service_map_vertex_pkey PRIMARY KEY (pk);


--
-- Name: stop stop_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.stop
    ADD CONSTRAINT stop_pkey PRIMARY KEY (pk);


--
-- Name: stop stop_system_pk_id_key; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.stop
    ADD CONSTRAINT stop_system_pk_id_key UNIQUE (system_pk, id);


--
-- Name: system system_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.system
    ADD CONSTRAINT system_pkey PRIMARY KEY (pk);


--
-- Name: system_update system_update_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.system_update
    ADD CONSTRAINT system_update_pkey PRIMARY KEY (pk);


--
-- Name: transfer transfer_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.transfer
    ADD CONSTRAINT transfer_pkey PRIMARY KEY (pk);


--
-- Name: transfers_config transfers_config_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.transfers_config
    ADD CONSTRAINT transfers_config_pkey PRIMARY KEY (pk);


--
-- Name: trip trip_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.trip
    ADD CONSTRAINT trip_pkey PRIMARY KEY (pk);


--
-- Name: trip trip_route_pk_id_key; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.trip
    ADD CONSTRAINT trip_route_pk_id_key UNIQUE (route_pk, id);


--
-- Name: trip_stop_time trip_stop_time_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.trip_stop_time
    ADD CONSTRAINT trip_stop_time_pkey PRIMARY KEY (pk);


--
-- Name: trip_stop_time trip_stop_time_trip_pk_stop_sequence_key; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.trip_stop_time
    ADD CONSTRAINT trip_stop_time_trip_pk_stop_sequence_key UNIQUE (trip_pk, stop_sequence);


--
-- Name: vehicle vehicle_pkey; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.vehicle
    ADD CONSTRAINT vehicle_pkey PRIMARY KEY (pk);


--
-- Name: vehicle vehicle_system_pk_id_key; Type: CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.vehicle
    ADD CONSTRAINT vehicle_system_pk_id_key UNIQUE (system_pk, id);


--
-- Name: direction_name_rule_stop_pk_priority_idx; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX direction_name_rule_stop_pk_priority_idx ON public.direction_name_rule USING btree (stop_pk, priority);


--
-- Name: feed_update_feed_pk_feed_update_pk_idx; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX feed_update_feed_pk_feed_update_pk_idx ON public.feed_update USING btree (feed_pk, pk);


--
-- Name: feed_update_status_result_completed_at_idx; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX feed_update_status_result_completed_at_idx ON public.feed_update USING btree (feed_pk, status, result, completed_at);


--
-- Name: feed_update_success_pk_completed_at_idx; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX feed_update_success_pk_completed_at_idx ON public.feed_update USING btree (feed_pk, completed_at) WHERE ((status)::text = 'SUCCESS'::text);


--
-- Name: idx_stop_system_pk_latitude; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX idx_stop_system_pk_latitude ON public.stop USING btree (system_pk, latitude);


--
-- Name: idx_stop_system_pk_longitude; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX idx_stop_system_pk_longitude ON public.stop USING btree (system_pk, longitude);


--
-- Name: ix_agency_source_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_agency_source_pk ON public.agency USING btree (source_pk);


--
-- Name: ix_alert_active_period_alert_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_active_period_alert_pk ON public.alert_active_period USING btree (alert_pk);


--
-- Name: ix_alert_agency_agency_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_agency_agency_pk ON public.alert_agency USING btree (agency_pk);


--
-- Name: ix_alert_agency_alert_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_agency_alert_pk ON public.alert_agency USING btree (alert_pk);


--
-- Name: ix_alert_message_alert_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_message_alert_pk ON public.alert_message USING btree (alert_pk);


--
-- Name: ix_alert_route_alert_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_route_alert_pk ON public.alert_route USING btree (alert_pk);


--
-- Name: ix_alert_route_route_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_route_route_pk ON public.alert_route USING btree (route_pk);


--
-- Name: ix_alert_source_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_source_pk ON public.alert USING btree (source_pk);


--
-- Name: ix_alert_stop_alert_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_stop_alert_pk ON public.alert_stop USING btree (alert_pk);


--
-- Name: ix_alert_stop_stop_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_stop_stop_pk ON public.alert_stop USING btree (stop_pk);


--
-- Name: ix_alert_system_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_system_pk ON public.alert USING btree (system_pk);


--
-- Name: ix_alert_trip_alert_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_trip_alert_pk ON public.alert_trip USING btree (alert_pk);


--
-- Name: ix_alert_trip_trip_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_alert_trip_trip_pk ON public.alert_trip USING btree (trip_pk);


--
-- Name: ix_direction_name_rule_source_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_direction_name_rule_source_pk ON public.direction_name_rule USING btree (source_pk);


--
-- Name: ix_route_source_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_route_source_pk ON public.route USING btree (source_pk);


--
-- Name: ix_scheduled_service_addition_service_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_scheduled_service_addition_service_pk ON public.scheduled_service_addition USING btree (service_pk);


--
-- Name: ix_scheduled_service_removal_service_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_scheduled_service_removal_service_pk ON public.scheduled_service_removal USING btree (service_pk);


--
-- Name: ix_scheduled_service_source_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_scheduled_service_source_pk ON public.scheduled_service USING btree (source_pk);


--
-- Name: ix_scheduled_service_system_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_scheduled_service_system_pk ON public.scheduled_service USING btree (system_pk);


--
-- Name: ix_service_map_route_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_service_map_route_pk ON public.service_map USING btree (route_pk);


--
-- Name: ix_stop_latitude; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_stop_latitude ON public.stop USING btree (latitude);


--
-- Name: ix_stop_longitude; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_stop_longitude ON public.stop USING btree (longitude);


--
-- Name: ix_stop_parent_stop_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_stop_parent_stop_pk ON public.stop USING btree (parent_stop_pk);


--
-- Name: ix_stop_source_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_stop_source_pk ON public.stop USING btree (source_pk);


--
-- Name: ix_system_id; Type: INDEX; Schema: public; Owner: transiter
--

CREATE UNIQUE INDEX ix_system_id ON public.system USING btree (id);


--
-- Name: ix_transfer_config_source_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_transfer_config_source_pk ON public.transfer USING btree (config_source_pk);


--
-- Name: ix_transfer_from_stop_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_transfer_from_stop_pk ON public.transfer USING btree (from_stop_pk);


--
-- Name: ix_transfer_source_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_transfer_source_pk ON public.transfer USING btree (source_pk);


--
-- Name: ix_transfer_system_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_transfer_system_pk ON public.transfer USING btree (system_pk);


--
-- Name: ix_transfer_to_stop_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_transfer_to_stop_pk ON public.transfer USING btree (to_stop_pk);


--
-- Name: ix_transfers_config_system_system_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_transfers_config_system_system_pk ON public.transfers_config_system USING btree (system_pk);


--
-- Name: ix_transfers_config_system_transfers_config_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_transfers_config_system_transfers_config_pk ON public.transfers_config_system USING btree (transfers_config_pk);


--
-- Name: ix_trip_source_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_trip_source_pk ON public.trip USING btree (source_pk);


--
-- Name: ix_vehicle_source_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_vehicle_source_pk ON public.vehicle USING btree (source_pk);


--
-- Name: ix_vehicle_system_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX ix_vehicle_system_pk ON public.vehicle USING btree (system_pk);


--
-- Name: ix_vehicle_trip_pk; Type: INDEX; Schema: public; Owner: transiter
--

CREATE UNIQUE INDEX ix_vehicle_trip_pk ON public.vehicle USING btree (trip_pk);


--
-- Name: scheduled_trip_stop_time_trip_pk_departure_time_idx; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX scheduled_trip_stop_time_trip_pk_departure_time_idx ON public.scheduled_trip_stop_time USING btree (trip_pk, departure_time);


--
-- Name: service_map_vertex_map_pk_position; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX service_map_vertex_map_pk_position ON public.service_map_vertex USING btree (map_pk, "position");


--
-- Name: system_update_system_pk_system_update_pk_idx; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX system_update_system_pk_system_update_pk_idx ON public.system_update USING btree (system_pk, pk);


--
-- Name: trip_stop_time_stop_pk_arrival_time_idx; Type: INDEX; Schema: public; Owner: transiter
--

CREATE INDEX trip_stop_time_stop_pk_arrival_time_idx ON public.trip_stop_time USING btree (stop_pk, arrival_time);


--
-- Name: agency agency_source_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.agency
    ADD CONSTRAINT agency_source_pk_fkey FOREIGN KEY (source_pk) REFERENCES public.feed_update(pk);


--
-- Name: agency agency_system_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.agency
    ADD CONSTRAINT agency_system_pk_fkey FOREIGN KEY (system_pk) REFERENCES public.system(pk);


--
-- Name: alert_active_period alert_active_period_alert_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert_active_period
    ADD CONSTRAINT alert_active_period_alert_pk_fkey FOREIGN KEY (alert_pk) REFERENCES public.alert(pk);


--
-- Name: alert_agency alert_agency_agency_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert_agency
    ADD CONSTRAINT alert_agency_agency_pk_fkey FOREIGN KEY (agency_pk) REFERENCES public.agency(pk);


--
-- Name: alert_agency alert_agency_alert_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert_agency
    ADD CONSTRAINT alert_agency_alert_pk_fkey FOREIGN KEY (alert_pk) REFERENCES public.alert(pk);


--
-- Name: alert_message alert_message_alert_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert_message
    ADD CONSTRAINT alert_message_alert_pk_fkey FOREIGN KEY (alert_pk) REFERENCES public.alert(pk);


--
-- Name: alert_route alert_route_alert_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert_route
    ADD CONSTRAINT alert_route_alert_pk_fkey FOREIGN KEY (alert_pk) REFERENCES public.alert(pk);


--
-- Name: alert_route alert_route_route_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert_route
    ADD CONSTRAINT alert_route_route_pk_fkey FOREIGN KEY (route_pk) REFERENCES public.route(pk);


--
-- Name: alert alert_source_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert
    ADD CONSTRAINT alert_source_pk_fkey FOREIGN KEY (source_pk) REFERENCES public.feed_update(pk);


--
-- Name: alert_stop alert_stop_alert_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert_stop
    ADD CONSTRAINT alert_stop_alert_pk_fkey FOREIGN KEY (alert_pk) REFERENCES public.alert(pk);


--
-- Name: alert_stop alert_stop_stop_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert_stop
    ADD CONSTRAINT alert_stop_stop_pk_fkey FOREIGN KEY (stop_pk) REFERENCES public.stop(pk);


--
-- Name: alert alert_system_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert
    ADD CONSTRAINT alert_system_pk_fkey FOREIGN KEY (system_pk) REFERENCES public.system(pk);


--
-- Name: alert_trip alert_trip_alert_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert_trip
    ADD CONSTRAINT alert_trip_alert_pk_fkey FOREIGN KEY (alert_pk) REFERENCES public.alert(pk);


--
-- Name: alert_trip alert_trip_trip_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.alert_trip
    ADD CONSTRAINT alert_trip_trip_pk_fkey FOREIGN KEY (trip_pk) REFERENCES public.trip(pk);


--
-- Name: direction_name_rule direction_name_rule_source_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.direction_name_rule
    ADD CONSTRAINT direction_name_rule_source_pk_fkey FOREIGN KEY (source_pk) REFERENCES public.feed_update(pk);


--
-- Name: direction_name_rule direction_name_rule_stop_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.direction_name_rule
    ADD CONSTRAINT direction_name_rule_stop_pk_fkey FOREIGN KEY (stop_pk) REFERENCES public.stop(pk);


--
-- Name: feed feed_system_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.feed
    ADD CONSTRAINT feed_system_pk_fkey FOREIGN KEY (system_pk) REFERENCES public.system(pk);


--
-- Name: feed_update feed_update_feed_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.feed_update
    ADD CONSTRAINT feed_update_feed_pk_fkey FOREIGN KEY (feed_pk) REFERENCES public.feed(pk);


--
-- Name: route route_agency_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.route
    ADD CONSTRAINT route_agency_pk_fkey FOREIGN KEY (agency_pk) REFERENCES public.agency(pk);


--
-- Name: route route_source_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.route
    ADD CONSTRAINT route_source_pk_fkey FOREIGN KEY (source_pk) REFERENCES public.feed_update(pk);


--
-- Name: route route_system_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.route
    ADD CONSTRAINT route_system_pk_fkey FOREIGN KEY (system_pk) REFERENCES public.system(pk);


--
-- Name: scheduled_service_addition scheduled_service_addition_service_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_service_addition
    ADD CONSTRAINT scheduled_service_addition_service_pk_fkey FOREIGN KEY (service_pk) REFERENCES public.scheduled_service(pk);


--
-- Name: scheduled_service_removal scheduled_service_removal_service_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_service_removal
    ADD CONSTRAINT scheduled_service_removal_service_pk_fkey FOREIGN KEY (service_pk) REFERENCES public.scheduled_service(pk);


--
-- Name: scheduled_service scheduled_service_source_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_service
    ADD CONSTRAINT scheduled_service_source_pk_fkey FOREIGN KEY (source_pk) REFERENCES public.feed_update(pk);


--
-- Name: scheduled_service scheduled_service_system_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_service
    ADD CONSTRAINT scheduled_service_system_pk_fkey FOREIGN KEY (system_pk) REFERENCES public.system(pk);


--
-- Name: scheduled_trip_frequency scheduled_trip_frequency_trip_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_trip_frequency
    ADD CONSTRAINT scheduled_trip_frequency_trip_pk_fkey FOREIGN KEY (trip_pk) REFERENCES public.scheduled_trip(pk);


--
-- Name: scheduled_trip scheduled_trip_route_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_trip
    ADD CONSTRAINT scheduled_trip_route_pk_fkey FOREIGN KEY (route_pk) REFERENCES public.route(pk);


--
-- Name: scheduled_trip scheduled_trip_service_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_trip
    ADD CONSTRAINT scheduled_trip_service_pk_fkey FOREIGN KEY (service_pk) REFERENCES public.scheduled_service(pk);


--
-- Name: scheduled_trip_stop_time scheduled_trip_stop_time_stop_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_trip_stop_time
    ADD CONSTRAINT scheduled_trip_stop_time_stop_pk_fkey FOREIGN KEY (stop_pk) REFERENCES public.stop(pk);


--
-- Name: scheduled_trip_stop_time scheduled_trip_stop_time_trip_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.scheduled_trip_stop_time
    ADD CONSTRAINT scheduled_trip_stop_time_trip_pk_fkey FOREIGN KEY (trip_pk) REFERENCES public.scheduled_trip(pk);


--
-- Name: service_map service_map_group_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.service_map
    ADD CONSTRAINT service_map_group_pk_fkey FOREIGN KEY (group_pk) REFERENCES public.service_map_group(pk);


--
-- Name: service_map_group service_map_group_system_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.service_map_group
    ADD CONSTRAINT service_map_group_system_pk_fkey FOREIGN KEY (system_pk) REFERENCES public.system(pk);


--
-- Name: service_map service_map_route_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.service_map
    ADD CONSTRAINT service_map_route_pk_fkey FOREIGN KEY (route_pk) REFERENCES public.route(pk);


--
-- Name: service_map_vertex service_map_vertex_map_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.service_map_vertex
    ADD CONSTRAINT service_map_vertex_map_pk_fkey FOREIGN KEY (map_pk) REFERENCES public.service_map(pk);


--
-- Name: service_map_vertex service_map_vertex_stop_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.service_map_vertex
    ADD CONSTRAINT service_map_vertex_stop_pk_fkey FOREIGN KEY (stop_pk) REFERENCES public.stop(pk);


--
-- Name: stop stop_parent_stop_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.stop
    ADD CONSTRAINT stop_parent_stop_pk_fkey FOREIGN KEY (parent_stop_pk) REFERENCES public.stop(pk);


--
-- Name: stop stop_source_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.stop
    ADD CONSTRAINT stop_source_pk_fkey FOREIGN KEY (source_pk) REFERENCES public.feed_update(pk);


--
-- Name: stop stop_system_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.stop
    ADD CONSTRAINT stop_system_pk_fkey FOREIGN KEY (system_pk) REFERENCES public.system(pk);


--
-- Name: system_update system_update_system_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.system_update
    ADD CONSTRAINT system_update_system_pk_fkey FOREIGN KEY (system_pk) REFERENCES public.system(pk);


--
-- Name: transfer transfer_config_source_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.transfer
    ADD CONSTRAINT transfer_config_source_pk_fkey FOREIGN KEY (config_source_pk) REFERENCES public.transfers_config(pk);


--
-- Name: transfer transfer_from_stop_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.transfer
    ADD CONSTRAINT transfer_from_stop_pk_fkey FOREIGN KEY (from_stop_pk) REFERENCES public.stop(pk);


--
-- Name: transfer transfer_source_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.transfer
    ADD CONSTRAINT transfer_source_pk_fkey FOREIGN KEY (source_pk) REFERENCES public.feed_update(pk);


--
-- Name: transfer transfer_system_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.transfer
    ADD CONSTRAINT transfer_system_pk_fkey FOREIGN KEY (system_pk) REFERENCES public.system(pk);


--
-- Name: transfer transfer_to_stop_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.transfer
    ADD CONSTRAINT transfer_to_stop_pk_fkey FOREIGN KEY (to_stop_pk) REFERENCES public.stop(pk);


--
-- Name: transfers_config_system transfers_config_system_system_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.transfers_config_system
    ADD CONSTRAINT transfers_config_system_system_pk_fkey FOREIGN KEY (system_pk) REFERENCES public.system(pk);


--
-- Name: transfers_config_system transfers_config_system_transfers_config_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.transfers_config_system
    ADD CONSTRAINT transfers_config_system_transfers_config_pk_fkey FOREIGN KEY (transfers_config_pk) REFERENCES public.transfers_config(pk);


--
-- Name: trip trip_route_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.trip
    ADD CONSTRAINT trip_route_pk_fkey FOREIGN KEY (route_pk) REFERENCES public.route(pk);


--
-- Name: trip trip_source_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.trip
    ADD CONSTRAINT trip_source_pk_fkey FOREIGN KEY (source_pk) REFERENCES public.feed_update(pk);


--
-- Name: trip_stop_time trip_stop_time_stop_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.trip_stop_time
    ADD CONSTRAINT trip_stop_time_stop_pk_fkey FOREIGN KEY (stop_pk) REFERENCES public.stop(pk);


--
-- Name: trip_stop_time trip_stop_time_trip_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.trip_stop_time
    ADD CONSTRAINT trip_stop_time_trip_pk_fkey FOREIGN KEY (trip_pk) REFERENCES public.trip(pk);


--
-- Name: vehicle vehicle_current_stop_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.vehicle
    ADD CONSTRAINT vehicle_current_stop_pk_fkey FOREIGN KEY (current_stop_pk) REFERENCES public.stop(pk);


--
-- Name: vehicle vehicle_source_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.vehicle
    ADD CONSTRAINT vehicle_source_pk_fkey FOREIGN KEY (source_pk) REFERENCES public.feed_update(pk);


--
-- Name: vehicle vehicle_system_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.vehicle
    ADD CONSTRAINT vehicle_system_pk_fkey FOREIGN KEY (system_pk) REFERENCES public.system(pk);


--
-- Name: vehicle vehicle_trip_pk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transiter
--

ALTER TABLE ONLY public.vehicle
    ADD CONSTRAINT vehicle_trip_pk_fkey FOREIGN KEY (trip_pk) REFERENCES public.trip(pk);


--
-- PostgreSQL database dump complete
--

