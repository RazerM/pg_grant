import sys
import typing as t
from enum import Enum
from typing import Any, List, Mapping, Optional, Sequence, Tuple, TypeVar, Union

from sqlalchemy import (
    ARRAY,
    Connection,
    Select,
    Text,
    cast,
    column,
    func,
    select,
    table,
    text,
)
from sqlalchemy.orm import Session

from ._typing_sqlalchemy import ArgTypesInput
from .exc import NoSuchObjectError
from .types import (
    ColumnInfo,
    FunctionInfo,
    ParameterInfo,
    RelationInfo,
    SchemaRelationInfo,
)

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

__all__ = (
    "get_all_table_acls",
    "get_table_acl",
    "get_all_column_acls",
    "get_column_acls",
    "get_all_sequence_acls",
    "get_sequence_acl",
    "get_all_function_acls",
    "get_function_acl",
    "get_all_language_acls",
    "get_language_acl",
    "get_all_schema_acls",
    "get_schema_acl",
    "get_all_database_acls",
    "get_database_acl",
    "get_all_tablespace_acls",
    "get_tablespace_acl",
    "get_all_type_acls",
    "get_type_acl",
    "get_all_parameter_acls",
    "get_parameter_acl",
)

pg_table_is_visible = func.pg_catalog.pg_table_is_visible
pg_function_is_visible = func.pg_catalog.pg_function_is_visible
pg_type_is_visible = func.pg_catalog.pg_type_is_visible
array_agg = func.array_agg
unnest = func.unnest
coalesce = func.coalesce
canonical_type = func.pg_temp.pg_grant_canonical_type

TP = TypeVar("TP", bound=Tuple[Any, ...])
Connectable: TypeAlias = Union[Connection, Session]


class PgRelKind(Enum):
    TABLE = "r"
    INDEX = "i"
    SEQUENCE = "S"
    VIEW = "v"
    MATERIALIZED_VIEW = "m"
    COMPOSITE_TYPE = "c"
    TOAST_TABLE = "t"
    FOREIGN_TABLE = "f"
    PARTITIONED_TABLE = "p"  # PostgresSQL 10+


pg_class = table(
    "pg_class",
    column("oid"),
    column("relname"),
    column("relacl"),
    column("relnamespace"),
    column("relkind"),
    column("relowner"),
)

pg_namespace = table(
    "pg_namespace",
    column("oid"),
    column("nspname"),
    column("nspowner"),
    column("nspacl"),
)

pg_roles = table(
    "pg_roles",
    column("oid"),
    column("rolname"),
)

pg_proc = table(
    "pg_proc",
    column("oid"),
    column("proname"),
    column("proargtypes"),
    column("pronamespace"),
    column("proacl"),
    column("proowner"),
)

pg_type = table(
    "pg_type",
    column("oid"),
    column("typname"),
    column("typnamespace"),
    column("typowner"),
    column("typacl"),
)

pg_parameter_acl = table(
    "pg_parameter_acl",
    column("oid"),
    column("parname"),
    column("paracl"),
)

pg_language = table(
    "pg_language",
    column("oid"),
    column("lanname"),
    column("lanowner"),
    column("lanacl"),
)

pg_database = table(
    "pg_database",
    column("oid"),
    column("datname"),
    column("datdba"),
    column("datacl"),
)

pg_tablespace = table(
    "pg_tablespace",
    column("oid"),
    column("spcname"),
    column("spcowner"),
    column("spcacl"),
)

pg_attribute = table(
    "pg_attribute",
    column("attrelid"),
    column("attname"),
    column("attnum"),
    column("attisdropped"),
    column("attacl"),
)

_pg_class_stmt = (
    select(
        pg_class.c.oid,
        pg_namespace.c.nspname.label("schema"),
        pg_class.c.relname.label("name"),
        pg_roles.c.rolname.label("owner"),
        cast(pg_class.c.relacl, ARRAY(Text)).label("acl"),
    )
    .outerjoin(pg_namespace, pg_class.c.relnamespace == pg_namespace.c.oid)
    .outerjoin(pg_roles, pg_class.c.relowner == pg_roles.c.oid)
)

_pg_attribute_stmt = (
    select(
        pg_class.c.oid.label("table_oid"),
        pg_namespace.c.nspname.label("schema"),
        pg_class.c.relname.label("table"),
        pg_attribute.c.attname.label("column"),
        pg_roles.c.rolname.label("owner"),
        cast(pg_attribute.c.attacl, ARRAY(Text)).label("acl"),
    )
    .select_from(pg_attribute)
    .join(pg_class, pg_attribute.c.attrelid == pg_class.c.oid)
    .outerjoin(pg_namespace, pg_class.c.relnamespace == pg_namespace.c.oid)
    .outerjoin(pg_roles, pg_class.c.relowner == pg_roles.c.oid)
    .where(pg_attribute.c.attnum > 0)
    .where(~pg_attribute.c.attisdropped)
    .where(
        # need to cast for PostgreSQL < 13 on psycopg3
        cast(pg_class.c.relkind, Text).in_(
            [
                PgRelKind.TABLE.value,
                PgRelKind.VIEW.value,
                PgRelKind.MATERIALIZED_VIEW.value,
                PgRelKind.PARTITIONED_TABLE.value,
                PgRelKind.FOREIGN_TABLE.value,
            ]
        )
    )
)

_upat = unnest(pg_proc.c.proargtypes).alias("upat")
_pg_proc_argtypes = (
    select(
        coalesce(array_agg(canonical_type(pg_type.c.typname)), cast([], ARRAY(Text)))
    )
    .join(_upat, _upat.column == pg_type.c.oid)
    .scalar_subquery()
)

_pg_proc_stmt = (
    select(
        pg_proc.c.oid,
        pg_namespace.c.nspname.label("schema"),
        pg_proc.c.proname.label("name"),
        _pg_proc_argtypes.label("arg_types"),
        pg_roles.c.rolname.label("owner"),
        cast(pg_proc.c.proacl, ARRAY(Text)).label("acl"),
    )
    .outerjoin(pg_namespace, pg_proc.c.pronamespace == pg_namespace.c.oid)
    .outerjoin(pg_roles, pg_proc.c.proowner == pg_roles.c.oid)
)

_pg_lang_stmt = (
    select(
        pg_language.c.oid,
        pg_language.c.lanname.label("name"),
        pg_roles.c.rolname.label("owner"),
        cast(pg_language.c.lanacl, ARRAY(Text)).label("acl"),
    )
    .select_from(pg_language)
    .outerjoin(pg_roles, pg_language.c.lanowner == pg_roles.c.oid)
)

_pg_schema_stmt = (
    select(
        pg_namespace.c.oid,
        pg_namespace.c.nspname.label("name"),
        pg_roles.c.rolname.label("owner"),
        cast(pg_namespace.c.nspacl, ARRAY(Text)).label("acl"),
    )
    .select_from(pg_namespace)
    .outerjoin(pg_roles, pg_namespace.c.nspowner == pg_roles.c.oid)
)

_pg_db_stmt = (
    select(
        pg_database.c.oid,
        pg_database.c.datname.label("name"),
        pg_roles.c.rolname.label("owner"),
        cast(pg_database.c.datacl, ARRAY(Text)).label("acl"),
    )
    .select_from(pg_database)
    .outerjoin(pg_roles, pg_database.c.datdba == pg_roles.c.oid)
)

_pg_tablespace_stmt = (
    select(
        pg_tablespace.c.oid,
        pg_tablespace.c.spcname.label("name"),
        pg_roles.c.rolname.label("owner"),
        cast(pg_tablespace.c.spcacl, ARRAY(Text)).label("acl"),
    )
    .select_from(pg_tablespace)
    .outerjoin(pg_roles, pg_tablespace.c.spcowner == pg_roles.c.oid)
)

_pg_type_stmt = (
    select(
        pg_type.c.oid,
        pg_namespace.c.nspname.label("schema"),
        pg_type.c.typname.label("name"),
        pg_roles.c.rolname.label("owner"),
        cast(pg_type.c.typacl, ARRAY(Text)).label("acl"),
    )
    .select_from(pg_type)
    .outerjoin(pg_namespace, pg_type.c.typnamespace == pg_namespace.c.oid)
    .outerjoin(pg_roles, pg_type.c.typowner == pg_roles.c.oid)
)

_pg_parameter_stmt = select(
    pg_parameter_acl.c.oid,
    pg_parameter_acl.c.parname.label("name"),
    cast(pg_parameter_acl.c.paracl, ARRAY(Text)).label("acl"),
)


def _filter_pg_class_stmt(
    stmt: Select[TP], schema: Optional[str] = None, rel_name: Optional[str] = None
) -> Select[TP]:
    if schema is not None:
        stmt = stmt.where(pg_namespace.c.nspname == schema)

    if rel_name is not None:
        if schema is None:
            # "pg_table_is_visible can also be used with views, materialized
            # views, indexes, sequences and foreign tables"
            stmt = stmt.where(pg_table_is_visible(pg_class.c.oid))

        stmt = stmt.where(pg_class.c.relname == rel_name)

    return stmt


def _filter_pg_proc_stmt(
    schema: Optional[str] = None,
    function_name: Optional[str] = None,
    arg_types: Optional[ArgTypesInput] = None,
) -> Select[Any]:
    stmt = _pg_proc_stmt

    if (function_name is None) != (arg_types is None):
        raise TypeError(
            "function_name and arg_types must both be specified"
        )  # pragma: no cover

    if schema is not None:
        stmt = stmt.where(pg_namespace.c.nspname == schema)

    if function_name is not None:
        assert arg_types is not None
        arg_types = list(arg_types)

        arg_types_sub: Any
        if arg_types:
            typs = func.unnest(cast(arg_types, ARRAY(Text))).alias("typs")
            arg_types_sub = (
                select(array_agg(canonical_type(typs.column)))
                .select_from(typs)
                .scalar_subquery()
            )
        else:
            arg_types_sub = cast([], ARRAY(Text))

        if schema is None:
            stmt = stmt.where(pg_function_is_visible(pg_proc.c.oid))
        stmt = stmt.where(pg_proc.c.proname == function_name)
        stmt = stmt.where(_pg_proc_argtypes == arg_types_sub)

    return stmt


def _filter_pg_type_stmt(
    schema: Optional[str] = None, type_name: Optional[str] = None
) -> Select[Any]:
    stmt = _pg_type_stmt

    if schema is not None:
        stmt = stmt.where(pg_namespace.c.nspname == schema)

    if type_name is not None:
        if schema is None:
            stmt = stmt.where(pg_type_is_visible(pg_type.c.oid))
        stmt = stmt.where(pg_type.c.typname == type_name)

    return stmt


def _table_stmt(
    schema: Optional[str] = None, table_name: Optional[str] = None
) -> Select[Any]:
    stmt = _filter_pg_class_stmt(_pg_class_stmt, schema=schema, rel_name=table_name)
    return stmt.where(
        # need to cast for PostgreSQL < 13 on psycopg3
        cast(pg_class.c.relkind, Text).in_(
            [
                PgRelKind.TABLE.value,
                PgRelKind.VIEW.value,
                PgRelKind.MATERIALIZED_VIEW.value,
                PgRelKind.PARTITIONED_TABLE.value,
                PgRelKind.FOREIGN_TABLE.value,
            ]
        )
    )


def _sequence_stmt(
    schema: Optional[str] = None, sequence_name: Optional[str] = None
) -> Select[Any]:
    stmt = _filter_pg_class_stmt(_pg_class_stmt, schema=schema, rel_name=sequence_name)
    return stmt.where(pg_class.c.relkind == PgRelKind.SEQUENCE.value)


def get_all_table_acls(
    conn: Connectable, schema: Optional[str] = None
) -> List[SchemaRelationInfo]:
    """Get privileges for all tables, views, materialized views, and foreign
    tables.

    Specify `schema` to limit the results to that schema.

    Returns:
        List of :class:`~.types.SchemaRelationInfo` objects.
    """
    stmt = _table_stmt(schema=schema)
    return [
        SchemaRelationInfo(**t.cast("Mapping[str, Any]", row))
        for row in conn.execute(stmt).mappings()
    ]


def get_table_acl(
    conn: Connectable, name: str, schema: Optional[str] = None
) -> SchemaRelationInfo:
    """Get privileges for the table, view, materialized view, or foreign table
    specified by `name`.

    If `schema` is not given, the table or view must be visible in the search
    path.

    Returns:
         :class:`~.types.SchemaRelationInfo`
    """
    stmt = _table_stmt(schema=schema, table_name=name)
    row = conn.execute(stmt).mappings().first()
    if row is None:
        raise NoSuchObjectError(name)
    return SchemaRelationInfo(**t.cast("Mapping[str, Any]", row))


def get_all_column_acls(
    conn: Connectable, schema: Optional[str] = None
) -> List[ColumnInfo]:
    """Get privileges for all table, view, materialized view, and foreign
    table columns.

    Specify `schema` to limit the results to that schema.

    Returns:
        List of :class:`~.types.ColumnInfo` objects.
    """
    stmt = _filter_pg_class_stmt(_pg_attribute_stmt, schema=schema)
    return [
        ColumnInfo(**t.cast("Mapping[str, Any]", row))
        for row in conn.execute(stmt).mappings()
    ]


def get_column_acls(
    conn: Connectable, table_name: str, schema: Optional[str] = None
) -> List[ColumnInfo]:
    """Get column privileges for the table, view, materialized view, or foreign
    table specified by `name`.

    If `schema` is not given, the table or view must be visible in the search
    path.

    Returns:
         List of :class:`~.types.ColumnInfo` objects.
    """
    stmt = _filter_pg_class_stmt(_pg_attribute_stmt, schema=schema, rel_name=table_name)
    rows = conn.execute(stmt).mappings().all()
    if not rows:
        raise NoSuchObjectError(table_name)
    return [ColumnInfo(**t.cast("Mapping[str, Any]", row)) for row in rows]


def get_all_sequence_acls(
    conn: Connectable, schema: Optional[str] = None
) -> List[SchemaRelationInfo]:
    """Unless `schema` is given, returns all sequences from all schemas.

    Returns:
        List of :class:`~.types.SchemaRelationInfo` objects.
    """
    stmt = _sequence_stmt(schema=schema)
    return [
        SchemaRelationInfo(**t.cast("Mapping[str, Any]", row))
        for row in conn.execute(stmt).mappings()
    ]


def get_sequence_acl(
    conn: Connectable, sequence: str, schema: Optional[str] = None
) -> SchemaRelationInfo:
    """If `schema` is not given, the sequence must be visible in the search
    path.

    Returns:
         :class:`~.types.SchemaRelationInfo`
    """
    stmt = _sequence_stmt(schema=schema, sequence_name=sequence)
    row = conn.execute(stmt).mappings().first()
    if row is None:
        raise NoSuchObjectError(sequence)
    return SchemaRelationInfo(**t.cast("Mapping[str, Any]", row))


def _make_canonical_type_function(conn: Connectable) -> None:
    """Create function which canonicalizes a type name, returning the input
    when casting to REGTYPE fails.

    E.g. casting the 'any' type fails. Normal examples include 'int4' -> 'integer'
    """
    # pg_temp is per-connection
    stmt = text(
        """
        CREATE OR REPLACE FUNCTION pg_temp.pg_grant_canonical_type(typname text)
        RETURNS text AS $$
        BEGIN
          BEGIN
            typname := typname::regtype::text;
          EXCEPTION WHEN syntax_error THEN
          END;
          RETURN typname;
        END;
        $$
        LANGUAGE plpgsql
        STABLE
        RETURNS NULL ON NULL INPUT;
    """
    )
    conn.execute(stmt)


def get_all_function_acls(
    conn: Connectable, schema: Optional[str] = None
) -> List[FunctionInfo]:
    """Unless `schema` is given, returns all functions from all schemas.

    Returns:
        List of :class:`~.types.FunctionInfo` objects.
    """
    _make_canonical_type_function(conn)
    stmt = _filter_pg_proc_stmt(schema=schema)
    return [
        FunctionInfo(**t.cast("Mapping[str, Any]", row))
        for row in conn.execute(stmt).mappings()
    ]


def get_function_acl(
    conn: Connectable,
    function_name: str,
    arg_types: ArgTypesInput,
    schema: Optional[str] = None,
) -> FunctionInfo:
    """If `schema` is not given, the function must be visible in the search path.

    Returns:
         :class:`~.types.FunctionInfo`
    """
    # We could ask the user to register an event on their connection pool which
    # creates this function on checkout, but that isn't a nice API for the
    # common case.
    _make_canonical_type_function(conn)

    if (function_name is None) != (arg_types is None):
        raise TypeError("function_name and arg_types must both be specified")

    if not isinstance(arg_types, Sequence) or isinstance(arg_types, str):
        raise TypeError("arg_types should be a sequence of strings, e.g. ['text']")

    stmt = _filter_pg_proc_stmt(schema, function_name, arg_types)
    row = conn.execute(stmt).mappings().first()
    if row is None:
        raise NoSuchObjectError(function_name)
    return FunctionInfo(**t.cast("Mapping[str, Any]", row))


def get_all_language_acls(conn: Connectable) -> List[RelationInfo]:
    """
    Returns:
        List of :class:`~.types.RelationInfo` objects.
    """
    return [
        RelationInfo(**t.cast("Mapping[str, Any]", row))
        for row in conn.execute(_pg_lang_stmt).mappings()
    ]


def get_language_acl(conn: Connectable, language: str) -> RelationInfo:
    """
    Returns:
         :class:`~.types.RelationInfo`
    """
    stmt = _pg_lang_stmt.where(pg_language.c.lanname == language)
    row = conn.execute(stmt).mappings().first()
    if row is None:
        raise NoSuchObjectError(language)
    return RelationInfo(**t.cast("Mapping[str, Any]", row))


def get_all_schema_acls(conn: Connectable) -> List[RelationInfo]:
    """
    Returns:
        List of :class:`~.types.RelationInfo` objects.
    """
    return [
        RelationInfo(**t.cast("Mapping[str, Any]", row))
        for row in conn.execute(_pg_schema_stmt).mappings()
    ]


def get_schema_acl(conn: Connectable, schema: str) -> RelationInfo:
    """
    Returns:
         :class:`~.types.RelationInfo`
    """
    stmt = _pg_schema_stmt.where(pg_namespace.c.nspname == schema)
    row = conn.execute(stmt).mappings().first()
    if row is None:
        raise NoSuchObjectError(schema)
    return RelationInfo(**t.cast("Mapping[str, Any]", row))


def get_all_database_acls(conn: Connectable) -> List[RelationInfo]:
    """
    Returns:
        List of :class:`~.types.RelationInfo` objects.
    """
    return [
        RelationInfo(**t.cast("Mapping[str, Any]", row))
        for row in conn.execute(_pg_db_stmt).mappings()
    ]


def get_database_acl(conn: Connectable, database: str) -> RelationInfo:
    """
    Returns:
         :class:`~.types.RelationInfo`
    """
    stmt = _pg_db_stmt.where(pg_database.c.datname == database)
    row = conn.execute(stmt).mappings().first()
    if row is None:
        raise NoSuchObjectError(database)
    return RelationInfo(**t.cast("Mapping[str, Any]", row))


def get_all_tablespace_acls(conn: Connectable) -> List[RelationInfo]:
    """
    Returns:
        List of :class:`~.types.RelationInfo` objects.
    """
    return [
        RelationInfo(**t.cast("Mapping[str, Any]", row))
        for row in conn.execute(_pg_tablespace_stmt).mappings()
    ]


def get_tablespace_acl(conn: Connectable, tablespace: str) -> RelationInfo:
    """
    Returns:
         :class:`~.types.RelationInfo`
    """
    stmt = _pg_tablespace_stmt.where(pg_tablespace.c.spcname == tablespace)
    row = conn.execute(stmt).mappings().first()
    if row is None:
        raise NoSuchObjectError(tablespace)
    return RelationInfo(**t.cast("Mapping[str, Any]", row))


def get_all_type_acls(
    conn: Connectable, schema: Optional[str] = None
) -> List[SchemaRelationInfo]:
    """Unless `schema` is given, returns all types from all schemas.

    Returns:
        List of :class:`~.types.SchemaRelationInfo` objects.
    """
    stmt = _filter_pg_type_stmt(schema=schema)
    return [
        SchemaRelationInfo(**t.cast("Mapping[str, Any]", row))
        for row in conn.execute(stmt).mappings()
    ]


def get_type_acl(
    conn: Connectable, type_name: str, schema: Optional[str] = None
) -> SchemaRelationInfo:
    """If `schema` is not given, the type must be visible in the search path.

    Returns:
         :class:`~.types.SchemaRelationInfo`
    """
    stmt = _filter_pg_type_stmt(schema=schema, type_name=type_name)
    row = conn.execute(stmt).mappings().first()
    if row is None:
        raise NoSuchObjectError(type_name)
    return SchemaRelationInfo(**t.cast("Mapping[str, Any]", row))


def get_all_parameter_acls(conn: Connectable) -> List[ParameterInfo]:
    """Return all parameters which have non-default ACLs.

    Returns:
        List of :class:`~.types.ParameterInfo` objects
    """
    return [
        ParameterInfo(**t.cast("Mapping[str, Any]", row))
        for row in conn.execute(_pg_parameter_stmt).mappings()
    ]


def get_parameter_acl(conn: Connectable, parameter: str) -> Optional[ParameterInfo]:
    """Return information of the given parameter.

    Returns:
        :class:`~.types.ParameterInfo` if the parameter exists and has
        non-default privileges, otherwise ``None``.
    """
    stmt = _pg_parameter_stmt.where(pg_parameter_acl.c.parname == parameter)
    row = conn.execute(stmt).mappings().first()
    if row is None:
        return None
    return ParameterInfo(**t.cast("Mapping[str, Any]", row))
