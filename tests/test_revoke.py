from unittest.mock import patch

import pytest
from sqlalchemy import Column, Integer, MetaData, Sequence, Table, table
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base

from pg_grant import PgObjectType, Privileges
from pg_grant.sql import revoke

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
    (['ALL'], 'alice', 'REVOKE ALL ON TABLE mytable FROM alice'),
    (['ALL'], 'PUBLIC', 'REVOKE ALL ON TABLE mytable FROM PUBLIC'),
    (['ALL'], 'public', 'REVOKE ALL ON TABLE mytable FROM public'),
    (['ALL'], 'grant', 'REVOKE ALL ON TABLE mytable FROM "grant"'),
    (['SELECT'], 'alice', 'REVOKE SELECT ON TABLE mytable FROM alice'),
    (['SELECT', 'INSERT'], 'alice', 'REVOKE SELECT, INSERT ON TABLE mytable FROM alice'),
])
def test_compile_revoke_table_privs(privs, grantee, compiled):
    statement = revoke(privs, PgObjectType.TABLE, 'mytable', grantee)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('target, schema, compiled', [
    ('t', None, 'REVOKE ALL ON TABLE t FROM alice'),
    ('user', None, 'REVOKE ALL ON TABLE "user" FROM alice'),
    ('t', 's', 'REVOKE ALL ON TABLE s.t FROM alice'),
    ('t', 'user', 'REVOKE ALL ON TABLE "user".t FROM alice'),
    (simple_table, None, 'REVOKE ALL ON TABLE users FROM alice'),
    (simple_table_kw, None, 'REVOKE ALL ON TABLE "user" FROM alice'),
    (full_table, None, 'REVOKE ALL ON TABLE users FROM alice'),
    (full_table_kw, None, 'REVOKE ALL ON TABLE "user" FROM alice'),
    (full_table_schema, None, 'REVOKE ALL ON TABLE s.users FROM alice'),
    (ModelA, None, 'REVOKE ALL ON TABLE "user" FROM alice'),
    (ModelB, None, 'REVOKE ALL ON TABLE s.users FROM alice'),
])
def test_compile_revoke_table_target(target, schema, compiled):
    statement = revoke(['ALL'], PgObjectType.TABLE, target, 'alice', schema=schema)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('revoke_option, compiled', [
    (True, 'REVOKE GRANT OPTION FOR ALL ON TABLE t FROM alice'),
    (False, 'REVOKE ALL ON TABLE t FROM alice'),
])
def test_compile_revoke_table_revoke_option(revoke_option, compiled):
    statement = revoke(['ALL'], PgObjectType.TABLE, 't', 'alice', revoke_option)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('target, schema, compiled', [
    ('t', None, 'REVOKE ALL ON SEQUENCE t FROM alice'),
    ('user', None, 'REVOKE ALL ON SEQUENCE "user" FROM alice'),
    ('t', 's', 'REVOKE ALL ON SEQUENCE s.t FROM alice'),
    ('t', 'user', 'REVOKE ALL ON SEQUENCE "user".t FROM alice'),
    (seq, None, 'REVOKE ALL ON SEQUENCE user_id FROM alice'),
    (seq_kw, None, 'REVOKE ALL ON SEQUENCE "user" FROM alice'),
    (seq_schema, None, 'REVOKE ALL ON SEQUENCE s.user_id FROM alice'),
])
def test_compile_revoke_sequence_target(target, schema, compiled):
    statement = revoke(['ALL'], PgObjectType.SEQUENCE, target, 'alice', schema=schema)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('target, schema, compiled', [
    ('t', None, 'REVOKE ALL ON TYPE t FROM alice'),
    ('user', None, 'REVOKE ALL ON TYPE "user" FROM alice'),
    ('t', 's', 'REVOKE ALL ON TYPE s.t FROM alice'),
    ('t', 'user', 'REVOKE ALL ON TYPE "user".t FROM alice'),
])
def test_compile_revoke_type_target(target, schema, compiled):
    statement = revoke(['ALL'], PgObjectType.TYPE, target, 'alice', schema=schema)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('target, arg_types, schema, compiled', [
    ('t', (), None, 'REVOKE ALL ON FUNCTION t() FROM alice'),
    ('user', (), None, 'REVOKE ALL ON FUNCTION "user"() FROM alice'),
    ('t', (), 's', 'REVOKE ALL ON FUNCTION s.t() FROM alice'),
    ('t', (), 'grant', 'REVOKE ALL ON FUNCTION "grant".t() FROM alice'),
    ('t', ('integer',), None, 'REVOKE ALL ON FUNCTION t(integer) FROM alice'),
    ('user', ('text', 'integer'), None,
     'REVOKE ALL ON FUNCTION "user"(text, integer) FROM alice'),
])
def test_compile_revoke_function_target(target, arg_types, schema, compiled):
    statement = revoke(
        ['ALL'], PgObjectType.FUNCTION, target, 'alice', schema=schema,
        arg_types=arg_types)
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('type, target, compiled', [
    (PgObjectType.LANGUAGE, 't', 'REVOKE ALL ON LANGUAGE t FROM alice'),
    (PgObjectType.LANGUAGE, 'user', 'REVOKE ALL ON LANGUAGE "user" FROM alice'),
    (PgObjectType.SCHEMA, 't', 'REVOKE ALL ON SCHEMA t FROM alice'),
    (PgObjectType.SCHEMA, 'user', 'REVOKE ALL ON SCHEMA "user" FROM alice'),
    (PgObjectType.DATABASE, 't', 'REVOKE ALL ON DATABASE t FROM alice'),
    (PgObjectType.DATABASE, 'user', 'REVOKE ALL ON DATABASE "user" FROM alice'),
    (PgObjectType.TABLESPACE, 't', 'REVOKE ALL ON TABLESPACE t FROM alice'),
    (PgObjectType.TABLESPACE, 'user', 'REVOKE ALL ON TABLESPACE "user" FROM alice'),
])
def test_compile_revoke_other_target(type, target, compiled):
    statement = revoke(['ALL'], type, target, 'alice')
    assert str(statement.compile(dialect=postgresql.dialect())) == compiled


@pytest.mark.parametrize('type, target, schema, arg_types', [
    (PgObjectType.TABLE, simple_table, 's', None),
    (PgObjectType.SEQUENCE, seq, 's', None),
    ('blah', 't', 's', None),
    (PgObjectType.SEQUENCE, 't', 's', ()),
    (PgObjectType.SEQUENCE, 't', 's', ('integer',)),
])
def test_compile_revoke_invalid(type, target, schema, arg_types):
    statement = revoke(
        ['ALL'], type, target, 'alice', schema=schema, arg_types=arg_types)
    with pytest.raises(ValueError):
        str(statement.compile(dialect=postgresql.dialect()))


@pytest.mark.parametrize('privs', [
    ['BLAH', 'SELECT'],
    ['BLAH'],
])
def test_compile_revoke_privs_invalid(privs):
    with pytest.raises(ValueError):
        str(revoke(privs, PgObjectType.TABLE, 't', 'alice'))


@pytest.mark.parametrize('grantee, privs, privswgo, type_, target, kw', [
    ('alice', ['SELECT', 'INSERT'], [], PgObjectType.FOREIGN_TABLE, 'table1', {}),
    ('alice', ['SELECT'], ['INSERT'], PgObjectType.TABLE, 'table2', {'schema': 's'}),
])
def test_privileges_as_revoke_statements(grantee, privs, privswgo, type_, target, kw):
    priv = Privileges(grantee, 'bob', privs, privswgo)

    def fake_revoke(*args, **kwargs):
        return args, kwargs

    patch_revoke = patch('pg_grant.sql.revoke', fake_revoke)

    with patch_revoke:
        r = priv.as_revoke_statements(type_, target, **kw)

    expected = []

    if privs:
        expected.append(((privs, type_, target, grantee), kw))

    if privswgo:
        expected.append(((privswgo, type_, target, grantee), kw))

    assert r == expected
