import re
import sys
from typing import Any, ClassVar, List, Optional, Tuple, Union, cast, overload

from sqlalchemy import FromClause, Sequence, inspect
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.compiler import SQLCompiler
from sqlalchemy.sql.expression import ClauseElement, Executable

from ._typing_sqlalchemy import AnyTarget, ArgTypesInput, TableTarget
from .types import PgObjectType

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

__all__ = (
    "grant",
    "revoke",
)

_re_valid_priv = re.compile(
    r"(SELECT|UPDATE|INSERT|DELETE|TRUNCATE|REFERENCES|TRIGGER|EXECUTE|USAGE"
    r"|CREATE|CONNECT|TEMPORARY|ALL)(?:\s+\((.*)\))?"
)


def _as_table(element: Any) -> FromClause:
    """Allow a Table or ORM model to be used as a table name."""
    insp = inspect(element, raiseerr=False)

    try:
        return cast(FromClause, insp.selectable)
    except AttributeError:
        raise ValueError("Expected table element.")


# This could accept Sequence[str] but I think there's more utility to
# `privileges="SELECT" being a type error than allowing it.
PrivilegesInput: TypeAlias = Union[List[str], Tuple[str], Literal["ALL"]]


class _GrantRevoke(Executable, ClauseElement):
    keyword: ClassVar[Optional[str]] = None

    _privileges: Tuple[str, ...]
    _priv_type: PgObjectType
    _target: AnyTarget
    _grantee: str
    _grant_option: bool
    _schema: Optional[str]
    _arg_types: Optional[Tuple[str, ...]]
    _quote_subname: bool

    def __init__(
        self,
        privileges: PrivilegesInput,
        type: PgObjectType,
        target: AnyTarget,
        grantee: str,
        *,
        grant_option: bool = False,
        schema: Optional[str] = None,
        arg_types: Optional[ArgTypesInput] = None,
        quote_subname: bool = True,
    ):
        if privileges == "ALL":
            privileges = ("ALL",)

        self._privileges = tuple(privileges)
        self._priv_type = type
        self._target = target
        self._grantee = grantee
        self._grant_option = grant_option
        self._schema = schema
        self._arg_types = None if arg_types is None else tuple(arg_types)
        self._quote_subname = quote_subname


class _Grant(_GrantRevoke):
    inherit_cache = False

    keyword = "GRANT"


class _Revoke(_GrantRevoke):
    inherit_cache = False

    keyword = "REVOKE"


@compiles(_GrantRevoke)  # type: ignore[no-untyped-call,misc]
def _pg_grant(element: _Grant, compiler: SQLCompiler, **kw: Any) -> str:
    target = element._target
    schema = element._schema
    arg_types = element._arg_types
    priv_type = element._priv_type

    preparer = compiler.preparer

    privs = []

    for priv in element._privileges:
        match = _re_valid_priv.match(priv)
        if match is None:
            raise ValueError(f"Privilege not valid: {priv}")

        subname = match.group(2)

        if subname is not None:
            if element._quote_subname:
                subname = preparer.quote(subname)

            privs.append(f"{match.group(1)} ({subname})")
        else:
            privs.append(match.group(1))

    priv = ", ".join(privs)

    str_target = None

    if isinstance(target, str):
        if schema is not None:
            str_target = preparer.quote_schema(schema) + "." + preparer.quote(target)
        else:
            str_target = preparer.quote(target)
    else:
        if schema is not None:
            raise ValueError("schema argument not supported unless target is a string.")

    if priv_type is not PgObjectType.FUNCTION and arg_types is not None:
        raise ValueError("arg_types argument not supported unless type is FUNCTION.")

    if priv_type is PgObjectType.TABLE:
        if str_target is not None:
            target = str_target
        else:
            target = compiler.process(_as_table(target), ashint=True)
    elif priv_type is PgObjectType.SEQUENCE:
        if str_target is not None:
            target = str_target
        else:
            target = preparer.format_sequence(target)  # type: ignore[no-untyped-call]
    elif priv_type is PgObjectType.TYPE:
        if str_target is None:
            target = compiler.process(target)  # type: ignore[arg-type]
        else:
            target = str_target
    elif priv_type is PgObjectType.FUNCTION:
        if str_target is None:
            target = compiler.process(target)  # type: ignore[arg-type]
        else:
            if arg_types is None:
                raise ValueError(
                    "Must use an empty sequence if function has "
                    "no arguments, not None."
                )

            str_arg_types = ", ".join([preparer.quote(t) for t in arg_types])
            target = f"{str_target}({str_arg_types})"
    elif isinstance(priv_type, PgObjectType):
        if str_target is None:
            target = compiler.process(target)  # type: ignore[arg-type]
        else:
            target = str_target
    else:
        raise ValueError(f"Unknown type: {priv_type}")

    is_grant = element.keyword == "GRANT"

    grantee = element._grantee

    if grantee.upper() != "PUBLIC":
        grantee = compiler.preparer.quote(grantee)

    return "{}{} {} ON {} {} {} {}{}".format(
        element.keyword,
        " GRANT OPTION FOR" if element._grant_option and not is_grant else "",
        priv,
        priv_type.value,
        target,
        "TO" if is_grant else "FROM",
        grantee,
        " WITH GRANT OPTION" if element._grant_option and is_grant else "",
    )


@overload
def grant(
    privileges: PrivilegesInput,
    type: Literal[
        PgObjectType.TABLE,
        PgObjectType.SEQUENCE,
        PgObjectType.LANGUAGE,
        PgObjectType.SCHEMA,
        PgObjectType.DATABASE,
        PgObjectType.TABLESPACE,
        PgObjectType.TYPE,
        PgObjectType.FOREIGN_DATA_WRAPPER,
        PgObjectType.FOREIGN_SERVER,
        PgObjectType.FOREIGN_TABLE,
        PgObjectType.LARGE_OBJECT,
    ],
    target: str,
    grantee: str,
    *,
    grant_option: bool = ...,
    schema: Optional[str] = ...,
    arg_types: Optional[ArgTypesInput] = ...,
    quote_subname: bool = ...,
) -> Executable:
    """This overload handles all cases where target and schema are strings
    except functions (see arg_types).
    """


@overload
def grant(
    privileges: PrivilegesInput,
    type: Literal[PgObjectType.TABLE],
    target: TableTarget,
    grantee: str,
    *,
    grant_option: bool = ...,
    schema: None = ...,
    arg_types: None = ...,
    quote_subname: bool = ...,
) -> Executable:
    ...


@overload
def grant(
    privileges: PrivilegesInput,
    type: Literal[PgObjectType.SEQUENCE],
    target: Sequence,
    grantee: str,
    *,
    grant_option: bool = ...,
    schema: None = ...,
    arg_types: None = ...,
    quote_subname: bool = ...,
) -> Executable:
    ...


@overload
def grant(
    privileges: PrivilegesInput,
    type: Literal[PgObjectType.FUNCTION],
    target: str,
    grantee: str,
    *,
    grant_option: bool = ...,
    schema: Optional[str] = ...,
    arg_types: ArgTypesInput,
    quote_subname: bool = ...,
) -> Executable:
    ...


def grant(
    privileges: PrivilegesInput,
    type: PgObjectType,
    target: AnyTarget,
    grantee: str,
    *,
    grant_option: bool = False,
    schema: Optional[str] = None,
    arg_types: Optional[ArgTypesInput] = None,
    quote_subname: bool = True,
) -> Executable:
    """GRANT statement that may be executed by SQLAlchemy.

    Parameters:
        privileges: List of privileges (or ``'ALL'``).
        type: PostgreSQL object type.
        target: Object name, or appropriate SQLAlchemy object (e.g.
                :class:`~sqlalchemy.schema.Table` or a declarative class).
        grantee: Role to receive privileges.
        grant_option: Whether the recipient may in turn grant these privileges
                      to others.
        schema: Optional schema, if `target` is a string.
        arg_types: Sequence of argument types for granting privileges on
                   functions. E.g. ``('int4', 'int4')`` or ``()``.
        quote_subname: Quote subname identifier in privileges, e.g.
                       ``'SELECT (user)'`` -> ``'SELECT ("user")``. This should
                       only be ``False`` if the subname is already a valid
                       identifier.

    .. seealso:: https://www.postgresql.org/docs/current/static/sql-grant.html
    """
    return _Grant(
        privileges,
        type,
        target,
        grantee,
        grant_option=grant_option,
        schema=schema,
        arg_types=arg_types,
        quote_subname=quote_subname,
    )


@overload
def revoke(
    privileges: PrivilegesInput,
    type: Literal[
        PgObjectType.TABLE,
        PgObjectType.SEQUENCE,
        PgObjectType.LANGUAGE,
        PgObjectType.SCHEMA,
        PgObjectType.DATABASE,
        PgObjectType.TABLESPACE,
        PgObjectType.TYPE,
        PgObjectType.FOREIGN_DATA_WRAPPER,
        PgObjectType.FOREIGN_SERVER,
        PgObjectType.FOREIGN_TABLE,
        PgObjectType.LARGE_OBJECT,
    ],
    target: str,
    grantee: str,
    *,
    grant_option: bool = ...,
    schema: Optional[str] = ...,
    arg_types: Optional[ArgTypesInput] = ...,
    quote_subname: bool = ...,
) -> Executable:
    """This overload handles all cases where target and schema are strings
    except functions (see arg_types).
    """


@overload
def revoke(
    privileges: PrivilegesInput,
    type: Literal[PgObjectType.TABLE],
    target: TableTarget,
    grantee: str,
    *,
    grant_option: bool = ...,
    schema: None = ...,
    arg_types: None = ...,
    quote_subname: bool = ...,
) -> Executable:
    ...


@overload
def revoke(
    privileges: PrivilegesInput,
    type: Literal[PgObjectType.SEQUENCE],
    target: Sequence,
    grantee: str,
    *,
    grant_option: bool = ...,
    schema: None = ...,
    arg_types: None = ...,
    quote_subname: bool = ...,
) -> Executable:
    ...


@overload
def revoke(
    privileges: PrivilegesInput,
    type: Literal[PgObjectType.FUNCTION],
    target: str,
    grantee: str,
    *,
    grant_option: bool = ...,
    schema: Optional[str] = ...,
    arg_types: ArgTypesInput,
    quote_subname: bool = ...,
) -> Executable:
    ...


def revoke(
    privileges: PrivilegesInput,
    type: PgObjectType,
    target: AnyTarget,
    grantee: str,
    *,
    grant_option: bool = False,
    schema: Optional[str] = None,
    arg_types: Optional[ArgTypesInput] = None,
    quote_subname: bool = True,
) -> Executable:
    """REVOKE statement that may be executed by SQLAlchemy.

    Parameters:
        privileges: List of privileges (or ``'ALL'``).
        type: PostgreSQL object type.
        target: Object name, or appropriate SQLAlchemy object (e.g.
                :class:`~sqlalchemy.schema.Table` or a declarative class).
        grantee: Role to lose privileges.
        grant_option: Whether to revoke the grant option for these privileges.
        schema: Optional schema, if `target` is a string.
        arg_types: Sequence of argument types for revoking privileges on
                   functions. E.g. ``('int4', 'int4')`` or ``()``.
        quote_subname: Quote subname identifier in privileges, e.g.
                       ``'SELECT (user)'`` -> ``'SELECT ("user")``. This should
                       only be ``False`` if the subname is already a valid
                       identifier.

    .. warning:: When ``grant_option=True``, only the grant option is revoked,
                 not the privilege(s).

    .. seealso:: https://www.postgresql.org/docs/current/static/sql-revoke.html

    """
    return _Revoke(
        privileges,
        type,
        target,
        grantee,
        grant_option=grant_option,
        schema=schema,
        arg_types=arg_types,
        quote_subname=quote_subname,
    )
