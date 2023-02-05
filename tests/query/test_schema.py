import pytest

from pg_grant import NoSuchObjectError
from pg_grant.query import get_all_schema_acls, get_schema_acl


def test_get_schema_acl(connection, expected_acls):
    """Find visible schemas matching ``name``."""
    for name, acls in expected_acls.items():
        schema = get_schema_acl(connection, name)
        assert schema.acl == acls


@pytest.fixture
def expected_acls(connection, request):
    if connection.connection.server_version >= 150000:
        return {
            # pg_database_owner is owner, public get usage on the public schema
            # by default
            'public': ['pg_database_owner=UC/pg_database_owner', '=U/pg_database_owner'],
            # schema1 has default privileges, so None is returned.
            'schema1': None,
        }
    else:
        return {
            # postgres is owner, public get access to the public schema by
            # default
            'public': ['postgres=UC/postgres', '=UC/postgres'],
            # schema1 has default privileges, so None is returned.
            'schema1': None,
        }


def test_get_all_schema_acls(connection, expected_acls):
    """Get all schemas in all schemas."""
    schemas = get_all_schema_acls(connection)

    tested = 0

    for schema in schemas:
        if schema.name not in expected_acls:
            continue

        assert schema.acl == expected_acls[schema.name]
        tested += 1

    assert tested == len(expected_acls)


def test_no_such_object(connection):
    with pytest.raises(NoSuchObjectError):
        get_schema_acl(connection, 'schema2')
