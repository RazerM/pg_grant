import sys
from enum import Enum
from typing import TYPE_CHECKING, Any, List, NoReturn, Optional, Tuple, overload

from attrs import Factory, converters, define, field

try:
    from ._typing_sqlalchemy import (
        AnyTarget,
        ArgTypesInput,
        ExecutableType,
        SequenceType,
        TableTarget,
    )
except ImportError:
    HAVE_SQLALCHEMY = False
else:
    HAVE_SQLALCHEMY = True

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class PgObjectType(Enum):
    """PostgreSQL object type."""

    TABLE = "TABLE"
    SEQUENCE = "SEQUENCE"
    FUNCTION = "FUNCTION"
    LANGUAGE = "LANGUAGE"
    SCHEMA = "SCHEMA"
    DATABASE = "DATABASE"
    TABLESPACE = "TABLESPACE"
    TYPE = "TYPE"
    DOMAIN = "DOMAIN"
    FOREIGN_DATA_WRAPPER = "FOREIGN DATA WRAPPER"
    FOREIGN_SERVER = "FOREIGN SERVER"
    FOREIGN_TABLE = "FOREIGN TABLE"
    LARGE_OBJECT = "LARGE OBJECT"
    PARAMETER = "PARAMETER"


@define
class Privileges:
    """Stores information from a parsed privilege string.

    .. seealso:: :func:`~.parse.parse_acl_item`
    """

    grantee: str
    grantor: str
    privs: List[str] = Factory(list)
    privswgo: List[str] = Factory(list)

    if TYPE_CHECKING or HAVE_SQLALCHEMY:

        @overload
        def as_grant_statements(
            self,
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
            *,
            schema: Optional[str] = ...,
            arg_types: Optional[ArgTypesInput] = ...,
            quote_subname: bool = ...,
        ) -> List[ExecutableType]:
            ...

        @overload
        def as_grant_statements(
            self,
            type: Literal[PgObjectType.TABLE],
            target: TableTarget,
            *,
            schema: None = ...,
            arg_types: None = ...,
            quote_subname: bool = ...,
        ) -> List[ExecutableType]:
            ...

        @overload
        def as_grant_statements(
            self,
            type: Literal[PgObjectType.SEQUENCE],
            target: SequenceType,
            *,
            schema: None = ...,
            arg_types: None = ...,
            quote_subname: bool = ...,
        ) -> List[ExecutableType]:
            ...

        @overload
        def as_grant_statements(
            self,
            type: Literal[PgObjectType.FUNCTION],
            target: str,
            *,
            schema: Optional[str] = ...,
            arg_types: ArgTypesInput,
            quote_subname: bool = ...,
        ) -> List[ExecutableType]:
            ...

        def as_grant_statements(
            self,
            type: PgObjectType,
            target: AnyTarget,
            *,
            schema: Optional[str] = None,
            arg_types: Optional[ArgTypesInput] = None,
            quote_subname: bool = True,
        ) -> List[ExecutableType]:
            """Return array of :func:`~.sql.grant` statements that can be executed
            to grant these privileges. Refer to the function documentation for the
            meaning of `target` and additional keyword arguments.

            .. note:: This requires installing with the ``sqlalchemy`` extra.
            """
            from .sql import _Grant as grant

            statements: List[ExecutableType] = []

            if self.privs:
                statements.append(
                    grant(
                        self.privs,
                        type,
                        target,
                        self.grantee,
                        schema=schema,
                        arg_types=arg_types,
                        quote_subname=quote_subname,
                    )
                )

            if self.privswgo:
                statements.append(
                    grant(
                        self.privswgo,
                        type,
                        target,
                        self.grantee,
                        grant_option=True,
                        schema=schema,
                        arg_types=arg_types,
                        quote_subname=quote_subname,
                    )
                )

            return statements

        @overload
        def as_revoke_statements(
            self,
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
            *,
            schema: Optional[str] = ...,
            arg_types: Optional[ArgTypesInput] = ...,
            quote_subname: bool = ...,
        ) -> List[ExecutableType]:
            ...

        @overload
        def as_revoke_statements(
            self,
            type: Literal[PgObjectType.TABLE],
            target: TableTarget,
            *,
            schema: None = ...,
            arg_types: None = ...,
            quote_subname: bool = ...,
        ) -> List[ExecutableType]:
            ...

        @overload
        def as_revoke_statements(
            self,
            type: Literal[PgObjectType.SEQUENCE],
            target: SequenceType,
            *,
            schema: None = ...,
            arg_types: None = ...,
            quote_subname: bool = ...,
        ) -> List[ExecutableType]:
            ...

        @overload
        def as_revoke_statements(
            self,
            type: Literal[PgObjectType.FUNCTION],
            target: str,
            *,
            schema: Optional[str] = ...,
            arg_types: ArgTypesInput,
            quote_subname: bool = ...,
        ) -> List[ExecutableType]:
            ...

        def as_revoke_statements(
            self,
            type: PgObjectType,
            target: AnyTarget,
            *,
            schema: Optional[str] = None,
            arg_types: Optional[ArgTypesInput] = None,
            quote_subname: bool = True,
        ) -> List[ExecutableType]:
            """Return array of :func:`~.sql.revoke` statements that can be executed
            to revoke these privileges. Refer to the function documentation for the
            meaning of `target` and additional keyword arguments.

            .. note::

                The statement for the `privswgo` privileges will revoke them
                fully, not only their grant options.

            .. note:: This requires installing with the ``sqlalchemy`` extra.
            """
            from .sql import _Revoke as revoke

            statements: List[ExecutableType] = []

            if self.privs:
                statements.append(
                    revoke(
                        self.privs,
                        type,
                        target,
                        self.grantee,
                        schema=schema,
                        arg_types=arg_types,
                        quote_subname=quote_subname,
                    )
                )

            if self.privswgo:
                statements.append(
                    revoke(
                        self.privswgo,
                        type,
                        target,
                        self.grantee,
                        schema=schema,
                        arg_types=arg_types,
                        quote_subname=quote_subname,
                    )
                )

            return statements

    else:

        def as_grant_statements(
            self,
            type: Any,
            target: Any,
            *,
            schema: Optional[str] = None,
            arg_types: Optional[Any] = None,
            quote_subname: bool = True,
        ) -> NoReturn:
            raise RuntimeError("Missing sqlalchemy extra")

        def as_revoke_statements(
            self,
            type: Any,
            target: Any,
            *,
            schema: Optional[str] = None,
            arg_types: Optional[Any] = None,
            quote_subname: bool = True,
        ) -> NoReturn:
            raise RuntimeError("Missing sqlalchemy extra")


@define(kw_only=True)
class RelationInfo:
    """Holds object information and privileges as queried using the
    :mod:`.query` submodule."""

    #: Row identifier.
    oid: int

    #: Name of the table, sequence, etc.
    name: str

    #: Owner of the relation.
    owner: str

    #: Access control list.
    acl: Optional[Tuple[str, ...]] = field(converter=converters.optional(tuple))


@define(kw_only=True)
class SchemaRelationInfo(RelationInfo):
    """Holds object information and privileges as queried using the
    :mod:`.query` submodule."""

    #: The name of the schema that contains this relation.
    schema: str


@define(kw_only=True)
class FunctionInfo(SchemaRelationInfo):
    """Holds object information and privileges as queried using the
    :mod:`.query` submodule."""

    #: Data types of the function arguments.
    arg_types: Tuple[str, ...] = field(converter=tuple)


@define(kw_only=True)
class ColumnInfo:
    """Holds object information and privileges as queried using the
    :mod:`.query` submodule."""

    #: Table identifier.
    table_oid: int

    #: The name of the schema that contains the table.
    schema: str

    #: Name of the table.
    table: str

    #: Name of the column.
    column: str

    #: Owner of the table.
    owner: str

    #: Column access control list.
    acl: Optional[Tuple[str, ...]] = field(converter=converters.optional(tuple))


@define(kw_only=True)
class ParameterInfo:
    """Holds object information and privileges as queried using the
    :mod:`.query` submodule."""

    #: Row identifier.
    oid: int

    #: Name of the table, sequence, etc.
    name: str

    #: Access control list.
    acl: Optional[Tuple[str, ...]] = field(converter=converters.optional(tuple))
