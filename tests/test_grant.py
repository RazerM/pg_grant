from unittest.mock import patch

import pytest
from sqlalchemy import Column, Integer, MetaData, Sequence, Table, table
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base

from pg_grant import PgObjectType, Privileges
from pg_grant.sql import grant

meta = MetaData()
Base = declarative_base()

simple_table = table('users')
simple_table_kw = table('user')
full_table = Table('users', meta)
full_table_kw = Table('user', meta)
full_table_schema = Table('users', meta, schema='s')
seq = Sequence('user_id')
seq_kw = Sequence('user')
seq_schema = Sequence('user_id', schema='s')


class ModelA(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)


class ModelB(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 's'}
    id = Column(Integer, primary_key=True)


@pytest.mark.parametrize('privs, grantee, compiled', [
    (['ALL'], 'alice', 'GRANT ALL ON TABLE mytable TO alice'),
    ('ALL', 'PUBLIC', 'GRANT ALL ON TABLE mytable TO PUBLIC'),
    (['ALL'], 'public', 'GRANT ALL ON TABLE mytable TO public'),
    (['ALL'], 'grant', 'GRANT ALL ON TABLE mytable TO "grant"'),
    (['SELECT'], 'alice', 'GRANT SELECT ON TABLE mytable TO alice'),
    (['SELECT', 'INSERT'], 'alice', 'GRANT SELECT, INSERT ON TABLE mytable TO alice'),
])
def test_compile_grant_table_privs(privs, grantee, compiled):
    statement = grant(privs, PgObjectType.TABLE, 'mytable', grantee)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('target, schema, compiled', [
    ('t', None, 'GRANT ALL ON TABLE t TO alice'),
    ('user', None, 'GRANT ALL ON TABLE "user" TO alice'),
    ('t', 's', 'GRANT ALL ON TABLE s.t TO alice'),
    ('t', 'grant', 'GRANT ALL ON TABLE "grant".t TO alice'),
    (simple_table, None, 'GRANT ALL ON TABLE users TO alice'),
    (simple_table_kw, None, 'GRANT ALL ON TABLE "user" TO alice'),
    (full_table, None, 'GRANT ALL ON TABLE users TO alice'),
    (full_table_kw, None, 'GRANT ALL ON TABLE "user" TO alice'),
    (full_table_schema, None, 'GRANT ALL ON TABLE s.users TO alice'),
    (ModelA, None, 'GRANT ALL ON TABLE "user" TO alice'),
    (ModelB, None, 'GRANT ALL ON TABLE s.users TO alice'),
])
def test_compile_grant_table_target(target, schema, compiled):
    statement = grant(
        ['ALL'], PgObjectType.TABLE, target, 'alice', schema=schema)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('grant_option, compiled', [
    (True, 'GRANT ALL ON TABLE t TO alice WITH GRANT OPTION'),
    (False, 'GRANT ALL ON TABLE t TO alice'),
])
def test_compile_grant_table_grant_option(grant_option, compiled):
    statement = grant(['ALL'], PgObjectType.TABLE, 't', 'alice', grant_option)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('target, schema, compiled', [
    ('t', None, 'GRANT ALL (a) ON TABLE t TO alice'),
    ('user', None, 'GRANT ALL (a) ON TABLE "user" TO alice'),
    ('t', 's', 'GRANT ALL (a) ON TABLE s.t TO alice'),
    ('t', 'grant', 'GRANT ALL (a) ON TABLE "grant".t TO alice'),
    (simple_table, None, 'GRANT ALL (a) ON TABLE users TO alice'),
    (simple_table_kw, None, 'GRANT ALL (a) ON TABLE "user" TO alice'),
    (full_table, None, 'GRANT ALL (a) ON TABLE users TO alice'),
    (full_table_kw, None, 'GRANT ALL (a) ON TABLE "user" TO alice'),
    (full_table_schema, None, 'GRANT ALL (a) ON TABLE s.users TO alice'),
    (ModelA, None, 'GRANT ALL (a) ON TABLE "user" TO alice'),
    (ModelB, None, 'GRANT ALL (a) ON TABLE s.users TO alice'),
])
def test_compile_grant_table_column(target, schema, compiled):
    statement = grant(
        ['ALL (a)'], PgObjectType.TABLE, target, 'alice', schema=schema)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('target, schema, compiled', [
    ('t', None, 'GRANT ALL ("user") ON TABLE t TO alice'),
])
def test_compile_grant_table_column_quote(target, schema, compiled):
    statement = grant(
        ['ALL (user)'], PgObjectType.TABLE, target, 'alice', schema=schema)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('target, schema, compiled', [
    ('t', None, 'GRANT ALL ("user") ON TABLE t TO alice'),
])
def test_compile_grant_table_column_quoted_already(target, schema, compiled):
    statement = grant(
        ['ALL ("user")'], PgObjectType.TABLE, target, 'alice', schema=schema,
        quote_subname=False)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('target, schema, compiled', [
    ('t', None, 'GRANT ALL ON SEQUENCE t TO alice'),
    ('user', None, 'GRANT ALL ON SEQUENCE "user" TO alice'),
    ('t', 's', 'GRANT ALL ON SEQUENCE s.t TO alice'),
    ('t', 'grant', 'GRANT ALL ON SEQUENCE "grant".t TO alice'),
    (seq, None, 'GRANT ALL ON SEQUENCE user_id TO alice'),
    (seq_kw, None, 'GRANT ALL ON SEQUENCE "user" TO alice'),
    (seq_schema, None, 'GRANT ALL ON SEQUENCE s.user_id TO alice'),
])
def test_compile_grant_sequence_target(target, schema, compiled):
    statement = grant(
        ['ALL'], PgObjectType.SEQUENCE, target, 'alice', schema=schema)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('target, schema, compiled', [
    ('t', None, 'GRANT ALL ON TYPE t TO alice'),
    ('user', None, 'GRANT ALL ON TYPE "user" TO alice'),
    ('t', 's', 'GRANT ALL ON TYPE s.t TO alice'),
    ('t', 'grant', 'GRANT ALL ON TYPE "grant".t TO alice'),
])
def test_compile_grant_type_target(target, schema, compiled):
    statement = grant(['ALL'], PgObjectType.TYPE, target, 'alice', schema=schema)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('target, arg_types, schema, compiled', [
    ('t', (), None, 'GRANT ALL ON FUNCTION t() TO alice'),
    ('user', (), None, 'GRANT ALL ON FUNCTION "user"() TO alice'),
    ('t', (), 's', 'GRANT ALL ON FUNCTION s.t() TO alice'),
    ('t', (), 'grant', 'GRANT ALL ON FUNCTION "grant".t() TO alice'),
    ('t', ('integer',), None, 'GRANT ALL ON FUNCTION t(integer) TO alice'),
    ('user', ('text', 'integer'), None,
     'GRANT ALL ON FUNCTION "user"(text, integer) TO alice'),
])
def test_compile_grant_function_target(target, arg_types, schema, compiled):
    statement = grant(
        ['ALL'], PgObjectType.FUNCTION, target, 'alice', schema=schema,
        arg_types=arg_types)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('type, target, compiled', [
    (PgObjectType.LANGUAGE, 't', 'GRANT ALL ON LANGUAGE t TO alice'),
    (PgObjectType.LANGUAGE, 'user', 'GRANT ALL ON LANGUAGE "user" TO alice'),
    (PgObjectType.SCHEMA, 't', 'GRANT ALL ON SCHEMA t TO alice'),
    (PgObjectType.SCHEMA, 'user', 'GRANT ALL ON SCHEMA "user" TO alice'),
    (PgObjectType.DATABASE, 't', 'GRANT ALL ON DATABASE t TO alice'),
    (PgObjectType.DATABASE, 'user', 'GRANT ALL ON DATABASE "user" TO alice'),
    (PgObjectType.TABLESPACE, 't', 'GRANT ALL ON TABLESPACE t TO alice'),
    (PgObjectType.TABLESPACE, 'user', 'GRANT ALL ON TABLESPACE "user" TO alice'),
])
def test_compile_grant_other_target(type, target, compiled):
    statement = grant(['ALL'], type, target, 'alice')
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('type, target, schema, arg_types', [
    (PgObjectType.TABLE, simple_table, 's', None),
    (PgObjectType.SEQUENCE, seq, 's', None),
    ('blah', 't', 's', None),
    (PgObjectType.SEQUENCE, 't', 's', ()),
    (PgObjectType.SEQUENCE, 't', 's', ('integer',)),
])
def test_compile_grant_invalid(type, target, schema, arg_types):
    statement = grant(
        ['ALL'], type, target, 'alice', schema=schema, arg_types=arg_types)
    with pytest.raises(ValueError):
        str(statement.compile(dialect=postgresql.dialect()))


@pytest.mark.parametrize('privs', [
    ['BLAH', 'SELECT'],
    ['BLAH'],
])
def test_compile_grant_privs_invalid(privs):
    with pytest.raises(ValueError):
        str(grant(privs, PgObjectType.TABLE, 't', 'alice'))


def test_compile_grant_function_privs_invalid():
    with pytest.raises(ValueError) as exc_info:
        str(grant(['ALL'], PgObjectType.FUNCTION, 'fun1', 'alice'))
    assert 'use an empty sequence' in exc_info.value.args[0]


@pytest.mark.parametrize('grantee, privs, privswgo, type_, target, kw', [
    ('alice', ['SELECT', 'INSERT'], [], PgObjectType.FOREIGN_TABLE, 'table1', {}),
    ('alice', ['SELECT'], ['INSERT'], PgObjectType.TABLE, 'table2', {'schema': 's'}),
])
def test_privileges_as_grant_statements(grantee, privs, privswgo, type_, target, kw):
    priv = Privileges(grantee, 'bob', privs, privswgo)

    def fake_grant(*args, **kwargs):
        return args, kwargs

    patch_grant = patch('pg_grant.sql.grant', fake_grant)

    with patch_grant:
        r = priv.as_grant_statements(type_, target, **kw)

    expected = []

    if privs:
        expected.append(((privs, type_, target, grantee), kw))

    if privswgo:
        gokw = kw.copy()
        gokw.update(grant_option=True)
        expected.append(((privswgo, type_, target, grantee), gokw))

    assert r == expected
