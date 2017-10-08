import pytest
from sqlalchemy import create_engine
from testcontainers import PostgresContainer as _PostgresContainer


class PostgresContainer(_PostgresContainer):
    POSTGRES_USER = 'alice'
    POSTGRES_DB = 'db1'


@pytest.fixture(scope='session')
def postgres_url():
    postgres_container = PostgresContainer("postgres:10")
    with postgres_container as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope='session')
def engine(postgres_url):
    return create_engine(postgres_url)


@pytest.fixture(scope='session')
def schema(engine):
    with open('schema.sql') as fp:
        engine.execute(fp.read())


@pytest.fixture
def connection(engine, schema):
    with engine.connect() as conn:
        yield conn
