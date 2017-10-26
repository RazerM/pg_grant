import pytest

from pg_grant import NoSuchObjectError
from pg_grant.query import get_all_column_acls, get_column_acls


expected_acls = {
    'public': {
        'table1': {
            'id': None,
        },
        'table2': {
            'id': None,
            'user': {'charlie=r/alice'},
        },
        'view1': {
            'id': None,
        },
        'view2': {
            'id': {'charlie=arwx/alice'},
            'user': None,
        },
        'mview1': {
            'id': None,
        },
    },
}


def as_set(v):
    if v is not None:
        return set(v)


@pytest.mark.parametrize('table_name, columns', expected_acls['public'].items())
def test_get_column_acls_visible(connection, table_name, columns):
    """Find columns for visible (i.e. in search path) tables matching
    ``table_name``.
    """
    column_acls = get_column_acls(connection, table_name)
    column_acls = {r.column: r.acl for r in column_acls}
    assert column_acls.keys() == columns.keys()

    for col, acl in columns.items():
        assert as_set(column_acls[col]) == acl


@pytest.mark.parametrize('schema, table_name, columns', [
    (schema, table_name, columns)
    for schema, d in expected_acls.items()
    for table_name, columns in d.items()
])
def test_get_column_acls_schema(connection, schema, table_name, columns):
    """Find columns for tables from ``schema`` matching ``name``."""
    column_acls = get_column_acls(connection, table_name, schema)
    column_acls = {r.column: r.acl for r in column_acls}
    assert column_acls.keys() == columns.keys()

    for col, acl in columns.items():
        assert as_set(column_acls[col]) == acl


def test_get_all_column_acls(connection):
    """Get all sequences in all schemas."""
    column_acls = get_all_column_acls(connection)
    schemas = {x.schema for x in column_acls}
    assert schemas == {'public', 'information_schema', 'pg_catalog'}

    tested = 0

    for row in column_acls:
        if row.schema not in expected_acls:
            continue

        if row.table not in expected_acls[row.schema]:
            continue

        assert as_set(row.acl) == expected_acls[row.schema][row.table][row.column]
        tested += 1

    assert tested == sum(len(w) for v in expected_acls.values() for w in v.values())


def test_no_such_object(connection):
    with pytest.raises(NoSuchObjectError):
        get_column_acls(connection, 'table3')
