--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: bts; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE bts (
    id serial NOT NULL,
    project_id integer,
    bug_list_url character varying,
    bug_detail_url character varying,
    name character varying,
    "type" character varying(50) NOT NULL
);


ALTER TABLE public.bts OWNER TO foss;

--
-- Name: bts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('bts', 'id'), 3, true);


--
-- Name: bug; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE bug (
    id bigserial NOT NULL,
    native_id integer NOT NULL,
    bts_id integer,
    title character varying NOT NULL,
    creation_time timestamp with time zone NOT NULL,
    modification_time timestamp with time zone,
    "type" character varying(10) DEFAULT 'bug'::character varying,
    submitter integer,
    status character varying(20) NOT NULL,
    severity character varying(20),
    flags character varying[],
    product character varying(50) NOT NULL,
    component character varying(50)
);


ALTER TABLE public.bug OWNER TO foss;

--
-- Name: bug_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('bug', 'id'), 20237, true);


--
-- Name: cccc_metrics; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE cccc_metrics (
    id bigserial NOT NULL,
    revision_id bigint,
    sloc integer,
    cloc integer,
    rejloc integer,
    cyclomatic integer,
    if integer,
    nom integer
);


ALTER TABLE public.cccc_metrics OWNER TO foss;

--
-- Name: cccc_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('cccc_metrics', 'id'), 202, true);


--
-- Name: cccc_module_metrics; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE cccc_module_metrics (
    id bigserial NOT NULL,
    revision_id bigint,
    path character varying,
    cbo integer,
    dit integer,
    noc integer,
    wmc integer,
    fanin integer,
    fanout integer,
    if integer
);


ALTER TABLE public.cccc_module_metrics OWNER TO foss;

--
-- Name: cccc_module_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('cccc_module_metrics', 'id'), 166358, true);


--
-- Name: diffstats_metrics; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE diffstats_metrics (
    id bigserial NOT NULL,
    revision_id bigint,
    files_changed integer,
    loc_add integer,
    loc_del integer
);


ALTER TABLE public.diffstats_metrics OWNER TO foss;

--
-- Name: diffstats_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('diffstats_metrics', 'id'), 455, true);


--
-- Name: filetypes; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE filetypes (
    id bigserial NOT NULL,
    revision_id bigint,
    path character varying,
    mime_type character varying,
    compression character varying
);


ALTER TABLE public.filetypes OWNER TO foss;

--
-- Name: filetypes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('filetypes', 'id'), 5574812, true);


--
-- Name: identifier; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE identifier (
    id bigserial NOT NULL,
    person_id integer,
    data character varying
);


ALTER TABLE public.identifier OWNER TO foss;

--
-- Name: identifier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('identifier', 'id'), 69574, true);


--
-- Name: mailinglist; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE mailinglist (
    id serial NOT NULL,
    project_id integer,
    name character varying,
    description character varying,
    url character varying
);


ALTER TABLE public.mailinglist OWNER TO foss;

--
-- Name: mailinglist_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('mailinglist', 'id'), 5, true);


--
-- Name: person; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE person (
    id serial NOT NULL,
    name character varying
);


ALTER TABLE public.person OWNER TO foss;

--
-- Name: person_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('person', 'id'), 33812, true);


--
-- Name: post; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE post (
    id bigserial NOT NULL,
    mailinglist_id integer,
    subject character varying,
    message_id character varying,
    "timestamp" timestamp with time zone,
    followup bigint[],
    "from" integer
);


ALTER TABLE public.post OWNER TO foss;

--
-- Name: post_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('post', 'id'), 690212, true);


--
-- Name: project; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE project (
    id serial NOT NULL,
    name character varying(50) NOT NULL
);


ALTER TABLE public.project OWNER TO foss;

--
-- Name: project_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('project', 'id'), 4, true);


--
-- Name: revision; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE revision (
    id bigserial NOT NULL,
    vcs_id integer,
    native_revision character varying(50),
    "timestamp" timestamp with time zone,
    author integer
);


ALTER TABLE public.revision OWNER TO foss;

--
-- Name: revision_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('revision', 'id'), 168492, true);


--
-- Name: static_metrics; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE static_metrics (
    id bigserial NOT NULL,
    revision_id bigint,
    "type" character varying(10),
    sloc integer,
    ploc integer,
    bloc integer,
    cloc integer,
    nom integer,
    cyclomatic integer,
    fanin_tot integer,
    fanout_tot integer
);


ALTER TABLE public.static_metrics OWNER TO foss;

--
-- Name: static_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('static_metrics', 'id'), 657, true);


--
-- Name: static_module_metrics; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE static_module_metrics (
    id bigserial NOT NULL,
    revision_id bigint,
    path character varying,
    sloc integer,
    ploc integer,
    bloc integer,
    cloc integer,
    cyclomatic integer,
    fanin integer,
    fanout integer
);


ALTER TABLE public.static_module_metrics OWNER TO foss;

--
-- Name: static_module_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('static_module_metrics', 'id'), 2212959, true);


--
-- Name: vcs; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE vcs (
    id serial NOT NULL,
    project_id integer,
    "type" character varying(10),
    url character varying
);


ALTER TABLE public.vcs OWNER TO foss;

--
-- Name: vcs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('vcs', 'id'), 4, true);


--
-- Name: website; Type: TABLE; Schema: public; Owner: foss; Tablespace: 
--

CREATE TABLE website (
    id serial NOT NULL,
    project_id integer,
    url character varying
);


ALTER TABLE public.website OWNER TO foss;

--
-- Name: website_id_seq; Type: SEQUENCE SET; Schema: public; Owner: foss
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('website', 'id'), 4, true);


--
-- Name: bts_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY bts
    ADD CONSTRAINT bts_pkey PRIMARY KEY (id);


--
-- Name: bug_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY bug
    ADD CONSTRAINT bug_pkey PRIMARY KEY (id);


--
-- Name: cccc_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY cccc_metrics
    ADD CONSTRAINT cccc_metrics_pkey PRIMARY KEY (id);


--
-- Name: cccc_module_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY cccc_module_metrics
    ADD CONSTRAINT cccc_module_metrics_pkey PRIMARY KEY (id);


--
-- Name: diffstats_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY diffstats_metrics
    ADD CONSTRAINT diffstats_metrics_pkey PRIMARY KEY (id);


--
-- Name: filetypes_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY filetypes
    ADD CONSTRAINT filetypes_pkey PRIMARY KEY (id);


--
-- Name: identifier_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY identifier
    ADD CONSTRAINT identifier_pkey PRIMARY KEY (id);


--
-- Name: mailinglist_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY mailinglist
    ADD CONSTRAINT mailinglist_pkey PRIMARY KEY (id);


--
-- Name: person_name_key; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY person
    ADD CONSTRAINT person_name_key UNIQUE (name);


--
-- Name: person_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY person
    ADD CONSTRAINT person_pkey PRIMARY KEY (id);


--
-- Name: post_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY post
    ADD CONSTRAINT post_pkey PRIMARY KEY (id);


--
-- Name: project_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY project
    ADD CONSTRAINT project_pkey PRIMARY KEY (id);


--
-- Name: revision_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY revision
    ADD CONSTRAINT revision_pkey PRIMARY KEY (id);


--
-- Name: static_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY static_metrics
    ADD CONSTRAINT static_metrics_pkey PRIMARY KEY (id);


--
-- Name: static_module_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY static_module_metrics
    ADD CONSTRAINT static_module_metrics_pkey PRIMARY KEY (id);


--
-- Name: vcs_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY vcs
    ADD CONSTRAINT vcs_pkey PRIMARY KEY (id);


--
-- Name: website_pkey; Type: CONSTRAINT; Schema: public; Owner: foss; Tablespace: 
--

ALTER TABLE ONLY website
    ADD CONSTRAINT website_pkey PRIMARY KEY (id);


--
-- Name: bts_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY bts
    ADD CONSTRAINT bts_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: bug_bts_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY bug
    ADD CONSTRAINT bug_bts_id_fkey FOREIGN KEY (bts_id) REFERENCES bts(id);


--
-- Name: bug_submitter_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY bug
    ADD CONSTRAINT bug_submitter_fkey FOREIGN KEY (submitter) REFERENCES person(id);


--
-- Name: cccc_metrics_revision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY cccc_metrics
    ADD CONSTRAINT cccc_metrics_revision_id_fkey FOREIGN KEY (revision_id) REFERENCES revision(id);


--
-- Name: cccc_module_metrics_revision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY cccc_module_metrics
    ADD CONSTRAINT cccc_module_metrics_revision_id_fkey FOREIGN KEY (revision_id) REFERENCES revision(id);


--
-- Name: diffstats_metrics_revision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY diffstats_metrics
    ADD CONSTRAINT diffstats_metrics_revision_id_fkey FOREIGN KEY (revision_id) REFERENCES revision(id);


--
-- Name: filetypes_revision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY filetypes
    ADD CONSTRAINT filetypes_revision_id_fkey FOREIGN KEY (revision_id) REFERENCES revision(id);


--
-- Name: identifier_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY identifier
    ADD CONSTRAINT identifier_person_id_fkey FOREIGN KEY (person_id) REFERENCES person(id) ON DELETE CASCADE;


--
-- Name: mailinglist_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY mailinglist
    ADD CONSTRAINT mailinglist_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: post_from_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY post
    ADD CONSTRAINT post_from_fkey FOREIGN KEY ("from") REFERENCES person(id) ON DELETE CASCADE;


--
-- Name: post_mailinglist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY post
    ADD CONSTRAINT post_mailinglist_id_fkey FOREIGN KEY (mailinglist_id) REFERENCES mailinglist(id) ON DELETE CASCADE;


--
-- Name: revision_author_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY revision
    ADD CONSTRAINT revision_author_fkey FOREIGN KEY (author) REFERENCES person(id);


--
-- Name: revision_vcs_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY revision
    ADD CONSTRAINT revision_vcs_id_fkey FOREIGN KEY (vcs_id) REFERENCES vcs(id);


--
-- Name: static_metrics_revision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY static_metrics
    ADD CONSTRAINT static_metrics_revision_id_fkey FOREIGN KEY (revision_id) REFERENCES revision(id);


--
-- Name: static_module_metrics_revision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY static_module_metrics
    ADD CONSTRAINT static_module_metrics_revision_id_fkey FOREIGN KEY (revision_id) REFERENCES revision(id);


--
-- Name: vcs_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY vcs
    ADD CONSTRAINT vcs_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE;


--
-- Name: website_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: foss
--

ALTER TABLE ONLY website
    ADD CONSTRAINT website_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE;


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

