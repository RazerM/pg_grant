from sqlalchemy import inspect
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import ClauseElement, Executable

from pg_grant.types import PgObjectType


__all__ = (
    'Grant',
    'Revoke',
)


def _as_table(element):
    """Allow a Table or ORM model to be used as a table name."""
    insp = inspect(element, raiseerr=False)

    try:
        return insp.selectable
    except AttributeError:
        raise ValueError('Expected table element.')


class _GrantRevoke(Executable, ClauseElement):
    _execution_options = Executable._execution_options.union({
        'autocommit': True
    })

    valid_privileges = {
        'SELECT',
        'UPDATE',
        'INSERT',
        'DELETE',
        'TRUNCATE',
        'REFERENCES',
        'TRIGGER',
        'EXECUTE',
        'USAGE',
        'CREATE',
        'CONNECT',
        'TEMPORARY',
        'ALL',
    }
    keyword = None

    def __init__(self, privileges, type: PgObjectType, target, grantee,
                 grant_option=False, schema=None, arg_types=None):
        invalid_privilegs = set(privileges) - self.valid_privileges

        if invalid_privilegs:
            raise ValueError(
                'Privileges not valid: {}'.format(', '.join(invalid_privilegs)))

        self.privileges = privileges
        self.priv_type = type
        self.target = target
        self.grantee = grantee
        self.grant_option = grant_option
        self.schema = schema
        self.arg_types = arg_types


class Grant(_GrantRevoke):
    keyword = 'GRANT'


class Revoke(_GrantRevoke):
    keyword = 'REVOKE'


@compiles(_GrantRevoke)
def pg_grant(element, compiler, **kw):
    priv = ', '.join(element.privileges)

    target = element.target
    schema = element.schema
    arg_types = element.arg_types
    priv_type = element.priv_type

    preparer = compiler.preparer

    str_target = None

    if isinstance(target, str):
        if schema is not None:
            str_target = preparer.quote_schema(schema) + '.' + preparer.quote(target)
        else:
            str_target = preparer.quote(target)
    else:
        if schema is not None:
            raise ValueError('schema argument not supported unless target is a string.')

    if priv_type is not PgObjectType.FUNCTION and arg_types is not None:
        raise ValueError('arg_types argument not supported unless type is FUNCTION.')

    if priv_type is PgObjectType.TABLE:
        if str_target is not None:
            target = str_target
        else:
            target = compiler.process(_as_table(target), ashint=True)
    elif priv_type is PgObjectType.SEQUENCE:
        if str_target is not None:
            target = str_target
        else:
            target = preparer.format_sequence(target)
    elif priv_type is PgObjectType.TYPE:
        if str_target is None:
            target = compiler.process(target)
        else:
            target = str_target
    elif priv_type is PgObjectType.FUNCTION:
        if str_target is None:
            target = compiler.process(target)
        else:
            str_arg_types = ', '.join([preparer.quote(t) for t in arg_types])
            target = '{}({})'.format(str_target, str_arg_types)
    elif isinstance(priv_type, PgObjectType):
        if str_target is None:
            target = compiler.process(target)
        else:
            target = str_target
    else:
        raise ValueError('Unknown type: {}'.format(priv_type))

    is_grant = element.keyword == 'GRANT'

    return '{}{} {} ON {} {} {} {}{}'.format(
        element.keyword,
        ' GRANT OPTION FOR' if element.grant_option and not is_grant else '',
        priv,
        priv_type.value,
        target,
        'TO' if is_grant else 'FROM',
        compiler.preparer.quote(element.grantee),
        ' WITH GRANT OPTION' if element.grant_option and is_grant else '',
    )