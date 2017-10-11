from pathlib import Path

import pytest
from sqlalchemy import create_engine
from testcontainers import PostgresContainer as _PostgresContainer

tests_dir = Path(__file__).parents[0].resolve()
test_schema_file = Path(tests_dir, 'data', 'test-schema.sql')


class PostgresContainer(_PostgresContainer):
    POSTGRES_USER = 'alice'
    POSTGRES_DB = 'db1'


@pytest.fixture(scope='session')
def postgres_url():
    postgres_container = PostgresContainer("postgres:latest")
    with postgres_container as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope='session')
def engine(postgres_url):
    return create_engine(postgres_url)


@pytest.fixture(scope='session')
def pg_schema(engine):
    with test_schema_file.open() as fp:
        engine.execute(fp.read())


@pytest.fixture
def connection(engine, pg_schema):
    with engine.connect() as conn:
        yield conn
