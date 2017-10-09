from enum import Enum

from sqlalchemy import (
    ARRAY, MetaData, Text, cast, column, func, select, table, text)

__all__ = (
    'get_all_table_acls',
    'get_table_acls',
    'get_all_sequence_acls',
    'get_sequence_acls',
    'get_all_function_acls',
    'get_all_language_acls',
    'get_language_acls',
    'get_all_schema_acls',
    'get_schema_acls',
    'get_all_database_acls',
    'get_database_acls',
    'get_all_tablespace_acls',
    'get_tablespace_acls',
    'get_all_type_acls',
    'get_type_acls',
)

pg_table_is_visible = func.pg_catalog.pg_table_is_visible
pg_function_is_visible = func.pg_catalog.pg_function_is_visible
pg_type_is_visible = func.pg_catalog.pg_type_is_visible
array_agg = func.array_agg
unnest = func.unnest


class PgRelKind(Enum):
    TABLE = 'r'
    SEQUENCE = 'S'


metadata = MetaData()
_did_autoload = False


pg_class = table(
    'pg_class',
    column('oid'),
    column('relname'),
    column('relacl'),
    column('relnamespace'),
    column('relkind'),
    column('relowner'),
)

pg_namespace = table(
    'pg_namespace',
    column('oid'),
    column('nspname'),
    column('nspowner'),
    column('nspacl'),
)

pg_roles = table(
    'pg_roles',
    column('oid'),
    column('rolname'),
)

pg_proc = table(
    'pg_proc',
    column('oid'),
    column('proname'),
    column('proargtypes'),
    column('pronamespace'),
    column('proacl'),
    column('proowner'),
)

pg_type = table(
    'pg_type',
    column('oid'),
    column('typname'),
    column('typnamespace'),
    column('typowner'),
    column('typacl'),
)

pg_language = table(
    'pg_language',
    column('oid'),
    column('lanname'),
    column('lanowner'),
    column('lanacl'),
)

pg_database = table(
    'pg_database',
    column('oid'),
    column('datname'),
    column('datdba'),
    column('datacl'),
)

pg_tablespace = table(
    'pg_tablespace',
    column('oid'),
    column('spcname'),
    column('spcowner'),
    column('spcacl'),
)

_pg_class_stmt = (
    select([
        pg_class.c.oid,
        pg_namespace.c.nspname.label('schema'),
        pg_class.c.relname.label('name'),
        pg_roles.c.rolname.label('owner'),
        cast(pg_class.c.relacl, ARRAY(Text)).label('acl'),
    ])
    .select_from(
        pg_class
        .outerjoin(pg_namespace, pg_class.c.relnamespace == pg_namespace.c.oid)
        .outerjoin(pg_roles, pg_class.c.relowner == pg_roles.c.oid)
    )
)

_pg_proc_stmt = (
    select([
        pg_proc.c.oid,
        pg_proc.c.proname.label('name'),
        (
            select([array_agg(pg_type.c.typname)])
            .select_from(
                unnest(pg_proc.c.proargtypes).alias('upat')
                .join(pg_type, text('upat') == pg_type.c.oid)
            )
            .as_scalar()
            .label('argtypes')
        ),
        pg_roles.c.rolname.label('owner'),
        cast(pg_proc.c.proacl, ARRAY(Text)).label('acl'),
    ])
    .select_from(
        pg_proc
        .outerjoin(pg_namespace, pg_proc.c.pronamespace == pg_namespace.c.oid)
        .outerjoin(pg_roles, pg_proc.c.proowner == pg_roles.c.oid)
    )
)

_pg_lang_stmt = (
    select([
        pg_language.c.oid,
        pg_language.c.lanname.label('name'),
        pg_roles.c.rolname.label('owner'),
        cast(pg_language.c.lanacl, ARRAY(Text)).label('acl'),
    ])
    .select_from(
        pg_language
        .outerjoin(pg_roles, pg_language.c.lanowner == pg_roles.c.oid)
    )
)

_pg_schema_stmt = (
    select([
        pg_namespace.c.oid,
        pg_namespace.c.nspname.label('name'),
        pg_roles.c.rolname.label('owner'),
        cast(pg_namespace.c.nspacl, ARRAY(Text)).label('acl'),
    ])
    .select_from(
        pg_namespace
        .outerjoin(pg_roles, pg_namespace.c.nspowner == pg_roles.c.oid)
    )
)

_pg_db_stmt = (
    select([
        pg_database.c.oid,
        pg_database.c.datname.label('name'),
        pg_roles.c.rolname.label('owner'),
        cast(pg_database.c.datacl, ARRAY(Text)).label('acl'),
    ])
    .select_from(
        pg_database
        .outerjoin(pg_roles, pg_database.c.datdba == pg_roles.c.oid)
    )
)

_pg_tablespace_stmt = (
    select([
        pg_tablespace.c.oid,
        pg_tablespace.c.spcname.label('name'),
        pg_roles.c.rolname.label('owner'),
        cast(pg_tablespace.c.spcacl, ARRAY(Text)).label('acl'),
    ])
    .select_from(
        pg_tablespace
        .outerjoin(pg_roles, pg_tablespace.c.spcowner == pg_roles.c.oid)
    )
)

_pg_type_stmt = (
    select([
        pg_type.c.oid,
        pg_type.c.typname.label('name'),
        pg_roles.c.rolname.label('owner'),
        cast(pg_type.c.typacl, ARRAY(Text)).label('acl'),
    ])
    .select_from(
        pg_type
        .outerjoin(pg_namespace, pg_type.c.typnamespace == pg_namespace.c.oid)
        .outerjoin(pg_roles, pg_type.c.typowner == pg_roles.c.oid)
    )
)


def _filter_pg_class_stmt(schema=None, rel_name=None):
    stmt = _pg_class_stmt

    if schema is not None:
        stmt = stmt.where(pg_namespace.c.nspname == schema)

    if rel_name is not None:
        if schema is None:
            # "pg_table_is_visible can also be used with views, materialized
            # views, indexes, sequences and foreign tables"
            stmt = stmt.where(pg_table_is_visible(pg_class.c.oid))

        stmt = stmt.where(pg_class.c.relname == rel_name)

    return stmt


def _filter_pg_proc_stmt(schema=None):
    # TODO: name + args
    stmt = _pg_proc_stmt

    if schema is not None:
        stmt = stmt.where(pg_namespace.c.nspname == schema)

    return stmt


def _filter_pg_type_stmt(schema=None, type_name=None):
    stmt = _pg_type_stmt

    if schema is not None:
        stmt = stmt.where(pg_namespace.c.nspname == schema)

    if type_name is not None:
        if schema is None:
            stmt = stmt.where(pg_type_is_visible(pg_type.c.oid))
        stmt = stmt.where(pg_type.c.typname == type_name)

    return stmt


def _table_stmt(schema=None, table_name=None):
    stmt = _filter_pg_class_stmt(schema=schema, rel_name=table_name)
    return stmt.where(pg_class.c.relkind == PgRelKind.TABLE.value)


def _sequence_stmt(schema=None, sequence_name=None):
    stmt = _filter_pg_class_stmt(schema=schema, rel_name=sequence_name)
    return stmt.where(pg_class.c.relkind == PgRelKind.SEQUENCE.value)


def get_all_table_acls(conn, schema=None):
    stmt = _table_stmt(schema=schema)
    return conn.execute(stmt).fetchall()


def get_table_acls(conn, table_name, schema=None):
    stmt = _table_stmt(schema=schema, table_name=table_name)
    return conn.execute(stmt).fetchone()


def get_all_sequence_acls(conn, schema=None):
    stmt = _sequence_stmt(schema=schema)
    print(stmt)
    return conn.execute(stmt).fetchall()


def get_sequence_acls(conn, sequence, schema=None):
    stmt = _sequence_stmt(schema=schema, sequence_name=sequence)
    return conn.execute(stmt).fetchone()


def get_all_function_acls(conn, schema=None):
    stmt = _filter_pg_proc_stmt(schema=schema)
    return conn.execute(stmt).fetchall()


def get_all_language_acls(conn):
    return conn.execute(_pg_lang_stmt).fetchall()


def get_language_acls(conn, language):
    stmt = _pg_lang_stmt.where(pg_language.c.lanname == language)
    return conn.execute(stmt).fetchone()


def get_all_schema_acls(conn):
    return conn.execute(_pg_schema_stmt).fetchall()


def get_schema_acls(conn, schema):
    stmt = _pg_schema_stmt.where(pg_namespace.c.nspname == schema)
    return conn.execute(stmt).fetchone()


def get_all_database_acls(conn):
    return conn.execute(_pg_db_stmt).fetchall()


def get_database_acls(conn, database):
    stmt = _pg_db_stmt.where(pg_database.c.datname == database)
    return conn.execute(stmt).fetchone()


def get_all_tablespace_acls(conn):
    return conn.execute(_pg_tablespace_stmt).fetchall()


def get_tablespace_acls(conn, tablespace):
    stmt = _pg_tablespace_stmt.where(pg_tablespace.c.spcname == tablespace)
    return conn.execute(stmt).fetchone()


def get_all_type_acls(conn, schema=None):
    stmt = _filter_pg_type_stmt(schema=schema)
    return conn.execute(stmt).fetchall()


def get_type_acls(conn, type_name, schema=None):
    stmt = _filter_pg_type_stmt(schema=schema, type_name=type_name)
    return conn.execute(stmt).fetchone()
