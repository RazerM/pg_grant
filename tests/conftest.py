import os
from contextlib import closing
from itertools import chain
from pathlib import Path

import psycopg2
from psycopg2 import sql
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

tests_dir = Path(__file__).parents[0].resolve()
test_schema_file = Path(tests_dir, 'data', 'test-schema.sql')

# This matches docker-compose.yml for easy local development
DEFAULT_DATABASE_URL = 'postgresql://postgres@127.0.0.1:5440/postgres'


@pytest.fixture(scope='session')
def postgres_url():
    # The only global state we want from the system is a superuser connection to
    # an empty database cluster.
    superuser_url = make_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))

    dbname = 'db1'
    superusers = ['alice']
    users = ['bob', 'charlie']
    password = 'hunter2'

    # We'll make a new database and roles in the cluster, so let's check that
    # they don't match that of the configured superuser url.
    assert superuser_url.username not in {*superusers, *users}
    assert superuser_url.database != dbname

    conn = psycopg2.connect(str(superuser_url))
    with closing(conn), conn.cursor() as cur:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        for user in superusers:
            stmt = sql.SQL("CREATE USER {} WITH SUPERUSER PASSWORD {}")
            cur.execute(stmt.format(sql.Identifier(user), sql.Literal(password)))
        for user in users:
            stmt = sql.SQL("CREATE USER {}")
            cur.execute(stmt.format(sql.Identifier(user)))
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))

    test_url = superuser_url.set(database=dbname, username=superusers[0], password=password)

    yield str(test_url)

    conn = psycopg2.connect(str(superuser_url))
    with closing(conn), conn.cursor() as cur:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(dbname)))
        for user in chain(superusers, users):
            user_ident = sql.Identifier(user)
            cur.execute(sql.SQL("DROP OWNED BY {} CASCADE").format(user_ident))
            cur.execute(sql.SQL("DROP USER {}").format(user_ident))


@pytest.fixture(scope='session')
def engine(postgres_url):
    engine = create_engine(postgres_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope='session')
def pg_schema(engine):
    with test_schema_file.open() as fp:
        with engine.connect() as conn:
            conn.execute(fp.read())


@pytest.fixture
def connection(engine, pg_schema):
    with engine.connect() as conn:
        yield conn
