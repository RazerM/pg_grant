import pytest

from pg_grant import NoSuchObjectError
from pg_grant.query import get_all_type_acls, get_type_acl


expected_acls = {
    'public': {
        # bug_status has default privileges, so None is returned.
        'bug_status': None,
        # alice is owner, bob was granted usage, public must get usage by default
        # https://stackoverflow.com/questions/46656644
        'thing': ['=U/alice', 'alice=U/alice', 'bob=U/alice'],
    },
}


@pytest.mark.parametrize('name, acls', expected_acls['public'].items())
def test_get_type_acl_visible(connection, name, acls):
    """Find visible (i.e. in search path) types matching ``name``."""
    type_ = get_type_acl(connection, name)
    assert type_.acl == acls


@pytest.mark.parametrize('schema, name, acls', [
    (schema, name, acl)
    for schema, d in expected_acls.items()
    for name, acl in d.items()
])
def test_get_type_acl_schema(connection, schema, name, acls):
    """Find types  from ``schema`` matching ``name``."""
    type_ = get_type_acl(connection, name, schema)
    assert type_.acl == acls


def test_get_all_type_acls(connection):
    """Get all sequences in all schemas."""
    types = get_all_type_acls(connection)
    schemas = {x.schema for x in types}
    assert schemas >= {'public', 'information_schema', 'pg_catalog'}

    tested = 0

    for type_ in types:
        if type_.schema not in expected_acls:
            continue

        if type_.name not in expected_acls[type_.schema]:
            continue

        assert type_.acl == expected_acls[type_.schema][type_.name]
        tested += 1

    assert tested == sum(len(v) for v in expected_acls.values())


def test_no_such_object(connection):
    with pytest.raises(NoSuchObjectError):
        get_type_acl(connection, 'db2')
