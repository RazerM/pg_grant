import pytest

from pg_grant.query import get_all_table_acls, get_table_acls


expected_acls = {
    'public': {
        # table1 has default privileges, so None is returned.
        'table1': None,
        # alice is owner, bob was granted all
        'table2': ['alice=arwdDxt/alice', 'bob=arwdDxt/alice'],
    },
}


@pytest.mark.parametrize('name, acls', expected_acls['public'].items())
def test_get_table_acls_visible(connection, name, acls):
    """Find visible (i.e. in search path) tables matching ``name``."""
    table = get_table_acls(connection, name)
    assert table.acl == acls


@pytest.mark.parametrize('schema, name, acls', [
    (schema, name, acl)
    for schema, d in expected_acls.items()
    for name, acl in d.items()
])
def test_get_table_acls_schema(connection, schema, name, acls):
    """Find tables  from ``schema`` matching ``name``."""
    table = get_table_acls(connection, name, schema)
    assert table.acl == acls


def test_get_all_table_acls(connection):
    """Get all sequences in all schemas."""
    tables = get_all_table_acls(connection)
    schemas = {x.schema for x in tables}
    assert schemas == {'public', 'information_schema', 'pg_catalog'}

    for table in tables:
        if table.schema not in expected_acls:
            continue

        if table.name not in expected_acls[table.schema]:
            continue

        assert table.acl == expected_acls[table.schema][table.name]
