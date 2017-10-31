import pytest

from pg_grant import NoSuchObjectError
from pg_grant.query import get_all_database_acls, get_database_acl


expected_acls = {
    # postgres is owner, public get TEMPORARY and CONNECT,
    # alice was granted CONNECT
    'db1': ['=Tc/postgres', 'postgres=CTc/postgres', 'alice=c*/postgres'],
    # postgres has default privileges, so None is returned.
    'postgres': None,
}


@pytest.mark.parametrize('name, acls', expected_acls.items())
def test_get_database_acl(connection, name, acls):
    """Find visible databases matching ``name``."""
    database = get_database_acl(connection, name)
    assert database.acl == acls


def test_get_all_database_acls(connection):
    """Get all databases in all databases."""
    databases = get_all_database_acls(connection)

    tested = 0

    for database in databases:
        if database.name not in expected_acls:
            continue

        assert database.acl == expected_acls[database.name]
        tested += 1

    assert tested == len(expected_acls)


def test_no_such_object(connection):
    with pytest.raises(NoSuchObjectError):
        get_database_acl(connection, 'db2')
