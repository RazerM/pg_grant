import pytest

from pg_grant import NoSuchObjectError
from pg_grant.query import get_all_tablespace_acls, get_tablespace_acl


expected_acls = {
    # pg_default has default privileges, so None is returned.
    'pg_default': None,
    # postgres is owner, alice was granted CONNECT
    'pg_global': ['postgres=C/postgres', 'alice=C/postgres'],
}


@pytest.mark.parametrize('name, acls', expected_acls.items())
def test_get_tablespace_acl(connection, name, acls):
    """Find visible tablespaces matching ``name``."""
    tablespace = get_tablespace_acl(connection, name)
    assert tablespace.acl == acls


def test_get_all_tablespace_acls(connection):
    """Get all tablespaces in all tablespaces."""
    tablespaces = get_all_tablespace_acls(connection)

    tested = 0

    for tablespace in tablespaces:
        if tablespace.name not in expected_acls:
            continue

        assert tablespace.acl == expected_acls[tablespace.name]
        tested += 1

    assert tested == len(expected_acls)


def test_no_such_object(connection):
    with pytest.raises(NoSuchObjectError):
        get_tablespace_acl(connection, 'eggs')
