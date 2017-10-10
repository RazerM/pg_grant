import pytest

from pg_grant import PgObjectType, Privileges, get_default_privileges


@pytest.mark.parametrize('type, public_priv', [
    (PgObjectType.TABLE, None),
    (PgObjectType.SEQUENCE, None),
    (PgObjectType.FUNCTION, ['EXECUTE']),
    (PgObjectType.LANGUAGE, ['USAGE']),
    (PgObjectType.SCHEMA, None),
    (PgObjectType.DATABASE, ['CONNECT', 'TEMPORARY']),
    (PgObjectType.TABLESPACE, None),
    (PgObjectType.TYPE, ['USAGE']),
    (PgObjectType.FOREIGN_DATA_WRAPPER, None),
    (PgObjectType.FOREIGN_SERVER, None),
    (PgObjectType.FOREIGN_TABLE, None),
    (PgObjectType.LARGE_OBJECT, None),
])
def test_default_privileges(type, public_priv):
    owner = 'alice'
    owner_priv = Privileges(grantee=owner, grantor=owner, privs=['ALL'])

    expected = [owner_priv]

    if public_priv:
        expected.append(Privileges(grantee='PUBLIC', grantor=owner, privs=public_priv))

    assert get_default_privileges(type, owner) == expected
