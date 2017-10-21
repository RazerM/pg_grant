from functools import partial

import pytest
from plumbum.cmd import pg_dump

from pg_grant import parse_acl_item, FunctionInfo, PgObjectType
from pg_grant.query import (
    get_all_function_acls, get_all_sequence_acls, get_all_table_acls,
    get_all_type_acls)


pytestmark = pytest.mark.nocontainer


def _priv_acls(conn, acls, type_, revoke):
    for obj in acls:
        arg_types = None
        if isinstance(obj, FunctionInfo):
            arg_types = obj.arg_types

        if obj.acl is not None:
            for acl in obj.acl:
                parsed = parse_acl_item(acl)

                if revoke:
                    statements = parsed.as_revoke_statements(
                        type_, obj.name, schema=obj.schema, arg_types=arg_types)
                else:
                    statements = parsed.as_grant_statements(
                        type_, obj.name, schema=obj.schema, arg_types=arg_types)

                for stmt in statements:
                    conn.execute(stmt)


grant_table_acls = partial(_priv_acls, type_=PgObjectType.TABLE, revoke=False)
revoke_table_acls = partial(_priv_acls, type_=PgObjectType.TABLE, revoke=True)
grant_sequence_acls = partial(_priv_acls, type_=PgObjectType.SEQUENCE, revoke=False)
revoke_sequence_acls = partial(_priv_acls, type_=PgObjectType.SEQUENCE, revoke=True)
grant_type_acls = partial(_priv_acls, type_=PgObjectType.TYPE, revoke=False)
revoke_type_acls = partial(_priv_acls, type_=PgObjectType.TYPE, revoke=True)
grant_function_acls = partial(_priv_acls, type_=PgObjectType.FUNCTION, revoke=False)
revoke_function_acls = partial(_priv_acls, type_=PgObjectType.FUNCTION, revoke=True)


@pytest.mark.parametrize('get, revoke, grant', [
    (get_all_table_acls, revoke_table_acls, grant_table_acls),
    (get_all_sequence_acls, revoke_sequence_acls, grant_sequence_acls),
    (get_all_type_acls, revoke_type_acls, grant_type_acls),
    (get_all_function_acls, revoke_function_acls, grant_function_acls),
])
def test_revoke_grant_schema_relations(connection, postgres_url, get, revoke, grant):
    cmd = pg_dump['--schema-only', postgres_url]

    code, dump1, _ = cmd.run()
    assert code == 0

    acls = get(connection, 'public')
    revoke(connection, acls)

    code, dump2, _ = cmd.run()
    assert code == 0
    assert dump1 != dump2

    grant(connection, acls)

    code, dump3, _ = cmd.run()
    assert code == 0

    assert dump1 == dump3
