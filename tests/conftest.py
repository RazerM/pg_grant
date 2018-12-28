from pathlib import Path

import pytest
import testing.postgresql
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from testcontainers.postgres import PostgresContainer as _PostgresContainer

tests_dir = Path(__file__).parents[0].resolve()
test_schema_file = Path(tests_dir, 'data', 'test-schema.sql')

SUPERUSER_NAME = 'alice'
DB_NAME = 'db1'


Postgresql = testing.postgresql.PostgresqlFactory(
    initdb_args='-U postgres -A trust',
    database=DB_NAME,
)


class PostgresContainer(_PostgresContainer):
    POSTGRES_USER = 'postgres'
    POSTGRES_DB = DB_NAME


def pytest_addoption(parser):
    parser.addoption(
        '--no-container', action='store_true',
        help='Use temporary PostgreSQL cluster without a container.')


def pytest_runtest_setup(item):
    if 'nocontainer' in item.keywords and not item.config.getoption('--no-container'):
        pytest.skip('Use --no-container to execute this test.')


@pytest.fixture(scope='session')
def postgres_url(request):
    no_container = request.config.getoption("--no-container")
    if no_container:
        postgresql = Postgresql()

        # Use superuser to create new superuser, then yield new connection URL
        url = make_url(postgresql.url())
        engine = create_engine(url)
        engine.execute('CREATE ROLE {} WITH SUPERUSER LOGIN'.format(SUPERUSER_NAME))
        engine.dispose()
        url.username = SUPERUSER_NAME

        yield str(url)
    else:
        postgres_container = PostgresContainer("postgres:latest")
        with postgres_container as postgres:
            # Use superuser to create new superuser, then yield new connection URL
            url = make_url(postgres.get_connection_url())
            engine = create_engine(url)
            engine.execute(
                text(
                    'CREATE ROLE {} WITH SUPERUSER LOGIN PASSWORD '
                    ':password'.format(SUPERUSER_NAME)
                ),
                password=postgres_container.POSTGRES_PASSWORD,
            )
            engine.dispose()
            url.username = SUPERUSER_NAME

            yield str(url)


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
