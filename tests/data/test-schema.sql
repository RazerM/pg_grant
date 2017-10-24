CREATE ROLE bob;
CREATE ROLE charlie;

CREATE TABLE table1 (
  id SERIAL PRIMARY KEY
);

CREATE TABLE table2 (
  id SERIAL PRIMARY KEY
);

CREATE VIEW view1 AS (SELECT * FROM table1);
CREATE VIEW view2 AS (SELECT * FROM table2);

CREATE MATERIALIZED VIEW mview1 AS (SELECT * FROM table1);

GRANT UPDATE, INSERT, DELETE, TRUNCATE, REFERENCES, TRIGGER ON table2 TO bob;
GRANT SELECT ON table2 TO bob WITH GRANT OPTION;
GRANT INSERT ON view2 TO bob;

CREATE SEQUENCE seq1;
CREATE SEQUENCE seq2;

GRANT ALL ON seq2 TO bob;

CREATE OR REPLACE FUNCTION fun1(integer) RETURNS integer
AS 'SELECT $1;'
LANGUAGE SQL
IMMUTABLE;

CREATE OR REPLACE FUNCTION fun1(text) RETURNS text
AS 'SELECT $1;'
LANGUAGE SQL
IMMUTABLE;

REVOKE EXECUTE ON FUNCTION fun1(text) FROM PUBLIC;

CREATE SCHEMA schema1;

CREATE SEQUENCE schema1.seq3;

REVOKE USAGE ON LANGUAGE plpgsql FROM PUBLIC;
GRANT USAGE ON LANGUAGE plpgsql TO alice;

GRANT CONNECT ON DATABASE db1 TO alice WITH GRANT OPTION;

GRANT CREATE ON TABLESPACE pg_global TO alice;

CREATE TYPE bug_status AS ENUM ('new', 'open', 'closed');
CREATE TYPE thing AS ENUM ('spam', 'eggs');

GRANT USAGE ON TYPE thing TO bob;
