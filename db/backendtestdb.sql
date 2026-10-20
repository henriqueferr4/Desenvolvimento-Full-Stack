--
-- PostgreSQL database dump
--

\restrict G0Dy3ILT3XEsS55n7GgFqXPpgtFWvXrDsRDS41XjeU5Yr8v9sDDFzk2jOZWh0Kk

-- Dumped from database version 17.11
-- Dumped by pg_dump version 17.11

-- Started on 2026-10-11 19:49:37

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 217 (class 1259 OID 16389)
-- Name: servidores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.servidores (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    cargo character varying(100) NOT NULL,
    uf character varying(2) NOT NULL,
    orgao character varying(100) NOT NULL
);


ALTER TABLE public.servidores OWNER TO postgres;

--
-- TOC entry 4787 (class 0 OID 16389)
-- Dependencies: 217
-- Data for Name: servidores; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.servidores (id, nome, cargo, uf, orgao) FROM stdin;
1	A da Silva	Primeiro no banco	RS	Banco de Dados
2	B da Silva	Irmão do A	RS	Banco de Dados
3	Fulano de Tal	Perito	RJ	Polícia Federal
4	João da Costa	Perito	MG	Polícia Federal
5	Getúlio Vargas	Presidente da República	DF	Governo Federal
6	Flask Gunicorn	Backend do Trabalho	RS	Sistemas para Internet 2
\.


--
-- TOC entry 4641 (class 2606 OID 16393)
-- Name: servidores servidores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servidores
    ADD CONSTRAINT servidores_pkey PRIMARY KEY (id);


-- Completed on 2026-10-11 19:49:37

--
-- PostgreSQL database dump complete
--

\unrestrict G0Dy3ILT3XEsS55n7GgFqXPpgtFWvXrDsRDS41XjeU5Yr8v9sDDFzk2jOZWh0Kk

