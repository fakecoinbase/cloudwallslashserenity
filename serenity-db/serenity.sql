-- Database generated with pgModeler (PostgreSQL Database Modeler).
-- pgModeler  version: 0.9.2_snapshot20191127
-- PostgreSQL version: 12.0
-- Project Site: pgmodeler.io
-- Model Author: ---


-- Database creation must be done outside a multicommand file.
-- These commands were put in this file only as a convenience.
-- -- object: serenity | type: DATABASE --
-- -- DROP DATABASE IF EXISTS serenity;
-- CREATE DATABASE serenity;
-- -- ddl-end --
-- 

-- object: serenity | type: SCHEMA --
-- DROP SCHEMA IF EXISTS serenity CASCADE;
CREATE SCHEMA serenity;
-- ddl-end --
-- ALTER SCHEMA serenity OWNER TO postgres;
-- ddl-end --

SET search_path TO pg_catalog,public,serenity;
-- ddl-end --

-- object: serenity.exchange_trade | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_trade CASCADE;
CREATE TABLE serenity.exchange_trade (
	exchange_id integer NOT NULL
);
-- ddl-end --
-- ALTER TABLE serenity.exchange_trade OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange_order | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_order CASCADE;
CREATE TABLE serenity.exchange_order (
	exchange_order_id integer NOT NULL,
	exchange_id integer NOT NULL,
	account_id_exchange_account integer NOT NULL,
	exchange_instrument_id integer NOT NULL,
	CONSTRAINT exchange_order_pk PRIMARY KEY (exchange_order_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_order OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange_fill | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_fill CASCADE;
CREATE TABLE serenity.exchange_fill (
	exchange_order_id integer NOT NULL
);
-- ddl-end --
-- ALTER TABLE serenity.exchange_fill OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange CASCADE;
CREATE TABLE serenity.exchange (
	exchange_id integer NOT NULL,
	exchange_code varchar(32) NOT NULL,
	description varchar(256) NOT NULL,
	CONSTRAINT exchange_pk PRIMARY KEY (exchange_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange OWNER TO postgres;
-- ddl-end --

-- object: exchange_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_order DROP CONSTRAINT IF EXISTS exchange_fk CASCADE;
ALTER TABLE serenity.exchange_order ADD CONSTRAINT exchange_fk FOREIGN KEY (exchange_id)
REFERENCES serenity.exchange (exchange_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_trade DROP CONSTRAINT IF EXISTS exchange_fk CASCADE;
ALTER TABLE serenity.exchange_trade ADD CONSTRAINT exchange_fk FOREIGN KEY (exchange_id)
REFERENCES serenity.exchange (exchange_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.exchange_account | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_account CASCADE;
CREATE TABLE serenity.exchange_account (
	account_id integer NOT NULL,
	exchange_id integer NOT NULL,
	CONSTRAINT exchange_account_pk PRIMARY KEY (account_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_account OWNER TO postgres;
-- ddl-end --

-- object: exchange_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_account DROP CONSTRAINT IF EXISTS exchange_fk CASCADE;
ALTER TABLE serenity.exchange_account ADD CONSTRAINT exchange_fk FOREIGN KEY (exchange_id)
REFERENCES serenity.exchange (exchange_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.exchange_quote | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_quote CASCADE;
CREATE TABLE serenity.exchange_quote (
	exchange_id integer NOT NULL
);
-- ddl-end --
-- ALTER TABLE serenity.exchange_quote OWNER TO postgres;
-- ddl-end --

-- object: exchange_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_quote DROP CONSTRAINT IF EXISTS exchange_fk CASCADE;
ALTER TABLE serenity.exchange_quote ADD CONSTRAINT exchange_fk FOREIGN KEY (exchange_id)
REFERENCES serenity.exchange (exchange_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity."order" | type: TABLE --
-- DROP TABLE IF EXISTS serenity."order" CASCADE;
CREATE TABLE serenity."order" (
	order_id integer NOT NULL,
	instrument_id integer NOT NULL,
	trading_account_id integer NOT NULL,
	tif_id integer,
	parent_order_id integer,
	price decimal,
	quantity decimal NOT NULL,
	order_type_id integer,
	CONSTRAINT order_pk PRIMARY KEY (order_id)

);
-- ddl-end --
-- ALTER TABLE serenity."order" OWNER TO postgres;
-- ddl-end --

-- object: serenity.fill | type: TABLE --
-- DROP TABLE IF EXISTS serenity.fill CASCADE;
CREATE TABLE serenity.fill (
	order_id_order integer
);
-- ddl-end --
-- ALTER TABLE serenity.fill OWNER TO postgres;
-- ddl-end --

-- object: order_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.fill DROP CONSTRAINT IF EXISTS order_fk CASCADE;
ALTER TABLE serenity.fill ADD CONSTRAINT order_fk FOREIGN KEY (order_id_order)
REFERENCES serenity."order" (order_id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_account_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_order DROP CONSTRAINT IF EXISTS exchange_account_fk CASCADE;
ALTER TABLE serenity.exchange_order ADD CONSTRAINT exchange_account_fk FOREIGN KEY (account_id_exchange_account)
REFERENCES serenity.exchange_account (account_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_order_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_fill DROP CONSTRAINT IF EXISTS exchange_order_fk CASCADE;
ALTER TABLE serenity.exchange_fill ADD CONSTRAINT exchange_order_fk FOREIGN KEY (exchange_order_id)
REFERENCES serenity.exchange_order (exchange_order_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.instrument | type: TABLE --
-- DROP TABLE IF EXISTS serenity.instrument CASCADE;
CREATE TABLE serenity.instrument (
	instrument_id integer NOT NULL,
	instrument_code varchar(32) NOT NULL,
	CONSTRAINT instrument_pk PRIMARY KEY (instrument_id)

);
-- ddl-end --
-- ALTER TABLE serenity.instrument OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange_instrument | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_instrument CASCADE;
CREATE TABLE serenity.exchange_instrument (
	exchange_instrument_id integer NOT NULL,
	instrument_id integer,
	exchange_instrument_code varchar(32) NOT NULL,
	CONSTRAINT exchange_instrument_pk PRIMARY KEY (exchange_instrument_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_instrument OWNER TO postgres;
-- ddl-end --

-- object: instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_instrument DROP CONSTRAINT IF EXISTS instrument_fk CASCADE;
ALTER TABLE serenity.exchange_instrument ADD CONSTRAINT instrument_fk FOREIGN KEY (instrument_id)
REFERENCES serenity.instrument (instrument_id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_instrument_uq | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_instrument DROP CONSTRAINT IF EXISTS exchange_instrument_uq CASCADE;
ALTER TABLE serenity.exchange_instrument ADD CONSTRAINT exchange_instrument_uq UNIQUE (instrument_id);
-- ddl-end --

-- object: instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS instrument_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT instrument_fk FOREIGN KEY (instrument_id)
REFERENCES serenity.instrument (instrument_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_order DROP CONSTRAINT IF EXISTS exchange_instrument_fk CASCADE;
ALTER TABLE serenity.exchange_order ADD CONSTRAINT exchange_instrument_fk FOREIGN KEY (exchange_instrument_id)
REFERENCES serenity.exchange_instrument (exchange_instrument_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.currency | type: TABLE --
-- DROP TABLE IF EXISTS serenity.currency CASCADE;
CREATE TABLE serenity.currency (
	currency_id integer NOT NULL,
	currency_code varchar(8) NOT NULL,
	CONSTRAINT currency_pk PRIMARY KEY (currency_id)

);
-- ddl-end --
-- ALTER TABLE serenity.currency OWNER TO postgres;
-- ddl-end --

-- object: serenity.currency_pair | type: TABLE --
-- DROP TABLE IF EXISTS serenity.currency_pair CASCADE;
CREATE TABLE serenity.currency_pair (
	currency_pair_id integer NOT NULL,
	base_currency_id integer NOT NULL,
	quote_currency_id integer NOT NULL,
	instrument_id integer NOT NULL,
	CONSTRAINT currency_pair_pk PRIMARY KEY (currency_pair_id)

);
-- ddl-end --
-- ALTER TABLE serenity.currency_pair OWNER TO postgres;
-- ddl-end --

-- object: instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.currency_pair DROP CONSTRAINT IF EXISTS instrument_fk CASCADE;
ALTER TABLE serenity.currency_pair ADD CONSTRAINT instrument_fk FOREIGN KEY (instrument_id)
REFERENCES serenity.instrument (instrument_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: currency_pair_uq | type: CONSTRAINT --
-- ALTER TABLE serenity.currency_pair DROP CONSTRAINT IF EXISTS currency_pair_uq CASCADE;
ALTER TABLE serenity.currency_pair ADD CONSTRAINT currency_pair_uq UNIQUE (instrument_id);
-- ddl-end --

-- object: serenity.trading_account | type: TABLE --
-- DROP TABLE IF EXISTS serenity.trading_account CASCADE;
CREATE TABLE serenity.trading_account (
	trading_account_id integer NOT NULL,
	trading_account_name varchar(256) NOT NULL,
	CONSTRAINT account_pk PRIMARY KEY (trading_account_id)

);
-- ddl-end --
-- ALTER TABLE serenity.trading_account OWNER TO postgres;
-- ddl-end --

-- object: trading_account_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS trading_account_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT trading_account_fk FOREIGN KEY (trading_account_id)
REFERENCES serenity.trading_account (trading_account_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.time_in_force | type: TABLE --
-- DROP TABLE IF EXISTS serenity.time_in_force CASCADE;
CREATE TABLE serenity.time_in_force (
	tif_id integer NOT NULL,
	tif_code varchar(32) NOT NULL,
	CONSTRAINT time_in_force_pk PRIMARY KEY (tif_id)

);
-- ddl-end --
-- ALTER TABLE serenity.time_in_force OWNER TO postgres;
-- ddl-end --

-- object: time_in_force_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS time_in_force_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT time_in_force_fk FOREIGN KEY (tif_id)
REFERENCES serenity.time_in_force (tif_id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.order_type | type: TABLE --
-- DROP TABLE IF EXISTS serenity.order_type CASCADE;
CREATE TABLE serenity.order_type (
	order_type_id integer NOT NULL,
	order_type_code varchar(32) NOT NULL,
	CONSTRAINT order_type_pk PRIMARY KEY (order_type_id)

);
-- ddl-end --
-- ALTER TABLE serenity.order_type OWNER TO postgres;
-- ddl-end --

-- object: order_type_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS order_type_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT order_type_fk FOREIGN KEY (order_type_id)
REFERENCES serenity.order_type (order_type_id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: parent_order_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS parent_order_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT parent_order_fk FOREIGN KEY (parent_order_id)
REFERENCES serenity."order" (order_id) MATCH FULL
ON DELETE NO ACTION ON UPDATE NO ACTION;
-- ddl-end --

-- object: base_currency_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.currency_pair DROP CONSTRAINT IF EXISTS base_currency_fk CASCADE;
ALTER TABLE serenity.currency_pair ADD CONSTRAINT base_currency_fk FOREIGN KEY (base_currency_id)
REFERENCES serenity.currency (currency_id) MATCH FULL
ON DELETE NO ACTION ON UPDATE NO ACTION;
-- ddl-end --

-- object: quote_currency_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.currency_pair DROP CONSTRAINT IF EXISTS quote_currency_fk CASCADE;
ALTER TABLE serenity.currency_pair ADD CONSTRAINT quote_currency_fk FOREIGN KEY (quote_currency_id)
REFERENCES serenity.currency (currency_id) MATCH FULL
ON DELETE NO ACTION ON UPDATE NO ACTION;
-- ddl-end --


