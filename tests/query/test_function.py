import pytest

from pg_grant.query import get_all_function_acls, get_function_acls


expected_acls = {
    'public': {
        # fun1 has default privileges, so None is returned.
        ('fun1', ('int4',)): None,
        # alice is owner, execute was revoked from public
        ('fun1', ('text',)): ['alice=X/alice'],
    },
}


@pytest.mark.parametrize('signature, acls', expected_acls['public'].items())
def test_get_function_acls_visible(connection, signature, acls):
    """Find visible (i.e. in search path) functions matching ``name``."""
    name, arg_types = signature
    function = get_function_acls(connection, name, arg_types)
    assert function.acl == acls


@pytest.mark.parametrize('schema, name, arg_types, acls', [
    (schema, name, arg_types, acl)
    for schema, d in expected_acls.items()
    for (name, arg_types), acl in d.items()
])
def test_get_function_acls_schema(connection, schema, name, arg_types, acls):
    """Find functions  from ``schema`` matching ``name``."""
    function = get_function_acls(connection, name, arg_types, schema)
    assert function.acl == acls


def test_get_all_function_acls(connection):
    """Get all sequences in all schemas."""
    functions = get_all_function_acls(connection)
    schemas = {x.schema for x in functions}
    assert schemas == {'public', 'information_schema', 'pg_catalog'}

    tested = 0

    for function in functions:
        if function.schema not in expected_acls:
            continue

        key = (function.name, tuple(function.argtypes))
        print(key)

        if key not in expected_acls[function.schema]:
            continue

        assert function.acl == expected_acls[function.schema][key]
        tested += 1

    assert tested == sum(len(v) for v in expected_acls.values())
