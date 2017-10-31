import pytest

from pg_grant import NoSuchObjectError
from pg_grant.query import get_all_schema_acls, get_schema_acl


expected_acls = {
    # postgres is owner, public get access to the public schema by default
    'public': ['postgres=UC/postgres', '=UC/postgres'],
    # schema1 has default privileges, so None is returned.
    'schema1': None,
}


@pytest.mark.parametrize('name, acls', expected_acls.items())
def test_get_schema_acl(connection, name, acls):
    """Find visible schemas matching ``name``."""
    schema = get_schema_acl(connection, name)
    assert schema.acl == acls


def test_get_all_schema_acls(connection):
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
