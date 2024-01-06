import pytest

from pg_grant.query import get_all_parameter_acls, get_parameter_acl

expected_acls = {
    # postgres is owner, alice was granted usage
    "log_min_duration_statement": ("postgres=sA/postgres", "alice=sA/postgres"),
}


@pytest.mark.parametrize("name, acls", expected_acls.items())
def test_get_parameter_acl(connection, name, acls):
    server_version = connection.connection.dbapi_connection.info.server_version
    if server_version < 150000:
        pytest.skip("Requires PostgreSQL 15+")
    parameter = get_parameter_acl(connection, name)
    assert parameter.acl == acls


def test_get_all_parameter_acls(connection):
    """Get all parameters with non-default ACLs."""
    server_version = connection.connection.dbapi_connection.info.server_version
    if server_version < 150000:
        pytest.skip("Requires PostgreSQL 15+")
    parameters = get_all_parameter_acls(connection)

    tested = 0

    for parameter in parameters:
        if parameter.name not in expected_acls:
            continue

        assert parameter.acl == expected_acls[parameter.name]
        tested += 1

    assert tested == len(expected_acls)


def test_no_privileges(connection):
    server_version = connection.connection.dbapi_connection.info.server_version
    if server_version < 150000:
        pytest.skip("Requires PostgreSQL 15+")
    assert get_parameter_acl(connection, "eggs") is None
