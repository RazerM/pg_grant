import pytest

from pg_grant import NoSuchObjectError
from pg_grant.query import get_all_table_acls, get_table_acl


expected_acls = {
    'public': {
        # table1 has default privileges, so None is returned.
        'table1': None,
        # alice is owner, bob was granted all
        'table2': {'alice=arwdDxt/alice', 'bob=ar*wdDxt/alice'},
        # view1 has default privileges, so None is returned.
        'view1': None,
        # alice is owner, bob was granted INSERT
        'view2': {'alice=arwdDxt/alice', 'bob=a/alice'},
        # mview1 has default privileges, so None is returned.
        'mview1': None,
    },
}


def as_set(v):
    if v is not None:
        return set(v)


@pytest.mark.parametrize('name, acls', expected_acls['public'].items())
def test_get_table_acl_visible(connection, name, acls):
    """Find visible (i.e. in search path) tables matching ``name``."""
    table = get_table_acl(connection, name)
    assert as_set(table.acl) == acls


@pytest.mark.parametrize('schema, name, acls', [
    (schema, name, acl)
    for schema, d in expected_acls.items()
    for name, acl in d.items()
])
def test_get_table_acl_schema(connection, schema, name, acls):
    """Find tables from ``schema`` matching ``name``."""
    table = get_table_acl(connection, name, schema)
    assert as_set(table.acl) == acls


def test_get_all_table_acls(connection):
    """Get all sequences in all schemas."""
    tables = get_all_table_acls(connection)
    schemas = {x.schema for x in tables}
    assert schemas == {'public', 'information_schema', 'pg_catalog'}

    tested = 0

    for table in tables:
        if table.schema not in expected_acls:
            continue

        if table.name not in expected_acls[table.schema]:
            continue

        assert as_set(table.acl) == expected_acls[table.schema][table.name]
        tested += 1

    assert tested == sum(len(v) for v in expected_acls.values())


def test_no_such_object(connection):
    with pytest.raises(NoSuchObjectError):
        get_table_acl(connection, 'table3')
