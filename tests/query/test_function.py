from contextlib import suppress

import pytest

from pg_grant import NoSuchObjectError
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

        key = (function.name, tuple(function.arg_types))
        print(key)

        if key not in expected_acls[function.schema]:
            continue

        assert function.acl == expected_acls[function.schema][key]
        tested += 1

    assert tested == sum(len(v) for v in expected_acls.values())


@pytest.mark.parametrize('function_name, arg_types', [
    (None, ('int4',)),
    ('fun1', None),
])
def test_missing_args(function_name, arg_types):
    with pytest.raises(TypeError) as exc_info:
        get_function_acls(None, function_name, arg_types)

    msg = 'function_name and arg_types must both be specified'
    assert exc_info.value.args[0] == msg


@pytest.mark.parametrize('arg_types', [
    'a string',
    dict(),
    1
])
def test_invalid_arg_types_parameter(arg_types):
    with pytest.raises(TypeError) as exc_info:
        get_function_acls(None, 'fun1', arg_types)

    msg = 'arg_types should be a sequence of strings'
    assert msg in exc_info.value.args[0]


@pytest.mark.parametrize('arg_types', [
    (),
    [],
    ['int4'],
    ('int4',),
])
def test_valid_arg_types_parameter(connection, arg_types):
    with suppress(NoSuchObjectError):
        get_function_acls(connection, 'fun1', arg_types)


def test_no_such_object(connection):
    with pytest.raises(NoSuchObjectError):
        get_function_acls(connection, 'fun2', [])
