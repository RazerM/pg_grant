import os
from itertools import chain
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

tests_dir = Path(__file__).parents[0].resolve()
test_schema_file = Path(tests_dir, "data", "test-schema.sql")
test_schema_15_file = Path(tests_dir, "data", "test-schema-15+.sql")

# This matches docker-compose.yml for easy local development
DEFAULT_DATABASE_URL = "postgresql://postgres@127.0.0.1:5440/postgres"


@pytest.fixture(scope="session")
def postgres_url():
    # The only global state we want from the system is a superuser connection to
    # an empty database cluster.
    superuser_url = make_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))

    dbname = "db1"
    superusers = ["alice"]
    users = ["bob", "charlie"]
    password = "hunter2"

    # We'll make a new database and roles in the cluster, so let's check that
    # they don't match that of the configured superuser url.
    assert superuser_url.username not in {*superusers, *users}
    assert superuser_url.database != dbname

    superuser_url_str = superuser_url.render_as_string(hide_password=False)
    with psycopg.connect(superuser_url_str) as conn, conn.cursor() as cur:
        conn.autocommit = True
        for user in superusers:
            stmt = sql.SQL("CREATE USER {} WITH SUPERUSER PASSWORD {}")
            cur.execute(stmt.format(sql.Identifier(user), sql.Literal(password)))
        for user in users:
            stmt = sql.SQL("CREATE USER {}")
            cur.execute(stmt.format(sql.Identifier(user)))
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))

    test_url = superuser_url.set(
        database=dbname, username=superusers[0], password=password
    )

    yield test_url.render_as_string(hide_password=False)

    with psycopg.connect(superuser_url_str) as conn, conn.cursor() as cur:
        conn.autocommit = True
        cur.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(dbname)))
        for user in chain(superusers, users):
            user_ident = sql.Identifier(user)
            cur.execute(sql.SQL("DROP OWNED BY {} CASCADE").format(user_ident))
            cur.execute(sql.SQL("DROP USER {}").format(user_ident))


@pytest.fixture(scope="session")
def engine(postgres_url):
    url = make_url(postgres_url).set(drivername="postgresql+psycopg")
    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def pg_schema(engine):
    with engine.begin() as conn:
        with test_schema_file.open() as fp:
            conn.execute(text(fp.read()))
        server_version = conn.connection.dbapi_connection.info.server_version
        if server_version >= 150000:
            with test_schema_15_file.open() as fp:
                conn.execute(text(fp.read()))


@pytest.fixture
def connection(engine, pg_schema):
    with engine.connect() as conn:
        yield conn
