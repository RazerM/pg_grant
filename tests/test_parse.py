import pytest

from pg_grant import PgObjectType, Privileges, parse_acl, parse_acl_item

parse_data = [
    ('alice=arwdDxt/alice', 'alice', 'alice',
     ['SELECT', 'UPDATE', 'INSERT', 'DELETE', 'TRUNCATE', 'REFERENCES',
      'TRIGGER'], []),
    ('alice=a*r*w*d*D*x*t*/alice', 'alice', 'alice', [],
     ['SELECT', 'UPDATE', 'INSERT', 'DELETE', 'TRUNCATE', 'REFERENCES',
      'TRIGGER']),
    ('bob=arwdDxt/alice', 'bob', 'alice',
     ['SELECT', 'UPDATE', 'INSERT', 'DELETE', 'TRUNCATE', 'REFERENCES',
      'TRIGGER'], []),
    ('=arwdDx*t/alice', 'PUBLIC', 'alice',
     ['SELECT', 'UPDATE', 'INSERT', 'DELETE', 'TRUNCATE', 'TRIGGER'],
     ['REFERENCES']),
    ('"odd=name"=a/alice', 'odd=name', 'alice', ['INSERT'], []),
    ('"esc""ape"=a/alice', 'esc"ape', 'alice', ['INSERT'], []),

    ('bob=a/alice', 'bob', 'alice', ['INSERT'], []),
    ('bob=r/alice', 'bob', 'alice', ['SELECT'], []),
    ('bob=w/alice', 'bob', 'alice', ['UPDATE'], []),
    ('bob=d/alice', 'bob', 'alice', ['DELETE'], []),
    ('bob=D/alice', 'bob', 'alice', ['TRUNCATE'], []),
    ('bob=x/alice', 'bob', 'alice', ['REFERENCES'], []),
    ('bob=t/alice', 'bob', 'alice', ['TRIGGER'], []),
    ('bob=X/alice', 'bob', 'alice', ['EXECUTE'], []),
    ('bob=U/alice', 'bob', 'alice', ['USAGE'], []),
    ('bob=C/alice', 'bob', 'alice', ['CREATE'], []),
    ('bob=c/alice', 'bob', 'alice', ['CONNECT'], []),
    ('bob=T/alice', 'bob', 'alice', ['TEMPORARY'], []),

    ('bob=a*/alice', 'bob', 'alice', [], ['INSERT']),
    ('bob=r*/alice', 'bob', 'alice', [], ['SELECT']),
    ('bob=w*/alice', 'bob', 'alice', [], ['UPDATE']),
    ('bob=d*/alice', 'bob', 'alice', [], ['DELETE']),
    ('bob=D*/alice', 'bob', 'alice', [], ['TRUNCATE']),
    ('bob=x*/alice', 'bob', 'alice', [], ['REFERENCES']),
    ('bob=t*/alice', 'bob', 'alice', [], ['TRIGGER']),
    ('bob=X*/alice', 'bob', 'alice', [], ['EXECUTE']),
    ('bob=U*/alice', 'bob', 'alice', [], ['USAGE']),
    ('bob=C*/alice', 'bob', 'alice', [], ['CREATE']),
    ('bob=c*/alice', 'bob', 'alice', [], ['CONNECT']),
    ('bob=T*/alice', 'bob', 'alice', [], ['TEMPORARY']),
]

parse_table_data = [
    ('alice=arwdDxt/alice', 'alice', 'alice', ['ALL'], []),
    ('alice=a*r*w*d*D*x*t*/alice', 'alice', 'alice', [], ['ALL']),
    ('bob=arwdDxt/alice', 'bob', 'alice', ['ALL'], []),
    ('bob=arwdDx/alice', 'bob', 'alice',
     ['SELECT', 'UPDATE', 'INSERT', 'REFERENCES', 'DELETE', 'TRUNCATE'], []),

    ('bob=a/alice', 'bob', 'alice', ['INSERT'], []),
    ('bob=r/alice', 'bob', 'alice', ['SELECT'], []),
    ('bob=w/alice', 'bob', 'alice', ['UPDATE'], []),
    ('bob=d/alice', 'bob', 'alice', ['DELETE'], []),
    ('bob=D/alice', 'bob', 'alice', ['TRUNCATE'], []),
    ('bob=x/alice', 'bob', 'alice', ['REFERENCES'], []),
    ('bob=t/alice', 'bob', 'alice', ['TRIGGER'], []),
    ('bob=X/alice', 'bob', 'alice', [], []),
    ('bob=U/alice', 'bob', 'alice', [], []),
    ('bob=C/alice', 'bob', 'alice', [], []),
    ('bob=c/alice', 'bob', 'alice', [], []),
    ('bob=T/alice', 'bob', 'alice', [], []),

    ('bob=a*/alice', 'bob', 'alice', [], ['INSERT']),
    ('bob=r*/alice', 'bob', 'alice', [], ['SELECT']),
    ('bob=w*/alice', 'bob', 'alice', [], ['UPDATE']),
    ('bob=d*/alice', 'bob', 'alice', [], ['DELETE']),
    ('bob=D*/alice', 'bob', 'alice', [], ['TRUNCATE']),
    ('bob=x*/alice', 'bob', 'alice', [], ['REFERENCES']),
    ('bob=t*/alice', 'bob', 'alice', [], ['TRIGGER']),
    ('bob=X*/alice', 'bob', 'alice', [], []),
    ('bob=U*/alice', 'bob', 'alice', [], []),
    ('bob=C*/alice', 'bob', 'alice', [], []),
    ('bob=c*/alice', 'bob', 'alice', [], []),
    ('bob=T*/alice', 'bob', 'alice', [], []),
]

parse_sequence_data = [
    ('alice=rwU/alice', 'alice', 'alice', ['ALL'], []),
    ('alice=r*w*U*/alice', 'alice', 'alice', [], ['ALL']),
    ('bob=rwU/alice', 'bob', 'alice', ['ALL'], []),
    ('bob=rw/alice', 'bob', 'alice', ['SELECT', 'UPDATE'], []),

    ('bob=a/alice', 'bob', 'alice', [], []),
    ('bob=r/alice', 'bob', 'alice', ['SELECT'], []),
    ('bob=w/alice', 'bob', 'alice', ['UPDATE'], []),
    ('bob=d/alice', 'bob', 'alice', [], []),
    ('bob=D/alice', 'bob', 'alice', [], []),
    ('bob=x/alice', 'bob', 'alice', [], []),
    ('bob=t/alice', 'bob', 'alice', [], []),
    ('bob=X/alice', 'bob', 'alice', [], []),
    ('bob=U/alice', 'bob', 'alice', ['USAGE'], []),
    ('bob=C/alice', 'bob', 'alice', [], []),
    ('bob=c/alice', 'bob', 'alice', [], []),
    ('bob=T/alice', 'bob', 'alice', [], []),

    ('bob=a*/alice', 'bob', 'alice', [], []),
    ('bob=r*/alice', 'bob', 'alice', [], ['SELECT']),
    ('bob=w*/alice', 'bob', 'alice', [], ['UPDATE']),
    ('bob=d*/alice', 'bob', 'alice', [], []),
    ('bob=D*/alice', 'bob', 'alice', [], []),
    ('bob=x*/alice', 'bob', 'alice', [], []),
    ('bob=t*/alice', 'bob', 'alice', [], []),
    ('bob=X*/alice', 'bob', 'alice', [], []),
    ('bob=U*/alice', 'bob', 'alice', [], ['USAGE']),
    ('bob=C*/alice', 'bob', 'alice', [], []),
    ('bob=c*/alice', 'bob', 'alice', [], []),
    ('bob=T*/alice', 'bob', 'alice', [], []),
]

parse_function_data = [
    ('alice=X/alice', 'alice', 'alice', ['ALL'], []),
    ('alice=X*/alice', 'alice', 'alice', [], ['ALL']),
    ('bob=X/alice', 'bob', 'alice', ['ALL'], []),

    ('bob=a/alice', 'bob', 'alice', [], []),
    ('bob=r/alice', 'bob', 'alice', [], []),
    ('bob=w/alice', 'bob', 'alice', [], []),
    ('bob=d/alice', 'bob', 'alice', [], []),
    ('bob=D/alice', 'bob', 'alice', [], []),
    ('bob=x/alice', 'bob', 'alice', [], []),
    ('bob=t/alice', 'bob', 'alice', [], []),
    ('bob=X/alice', 'bob', 'alice', ['ALL'], []),
    ('bob=U/alice', 'bob', 'alice', [], []),
    ('bob=C/alice', 'bob', 'alice', [], []),
    ('bob=c/alice', 'bob', 'alice', [], []),
    ('bob=T/alice', 'bob', 'alice', [], []),

    ('bob=a*/alice', 'bob', 'alice', [], []),
    ('bob=r*/alice', 'bob', 'alice', [], []),
    ('bob=w*/alice', 'bob', 'alice', [], []),
    ('bob=d*/alice', 'bob', 'alice', [], []),
    ('bob=D*/alice', 'bob', 'alice', [], []),
    ('bob=x*/alice', 'bob', 'alice', [], []),
    ('bob=t*/alice', 'bob', 'alice', [], []),
    ('bob=X*/alice', 'bob', 'alice', [], ['ALL']),
    ('bob=U*/alice', 'bob', 'alice', [], []),
    ('bob=C*/alice', 'bob', 'alice', [], []),
    ('bob=c*/alice', 'bob', 'alice', [], []),
    ('bob=T*/alice', 'bob', 'alice', [], []),
]

parse_language_data = [
    ('alice=U/alice', 'alice', 'alice', ['ALL'], []),
    ('alice=U*/alice', 'alice', 'alice', [], ['ALL']),
    ('bob=U/alice', 'bob', 'alice', ['ALL'], []),

    ('bob=a/alice', 'bob', 'alice', [], []),
    ('bob=r/alice', 'bob', 'alice', [], []),
    ('bob=w/alice', 'bob', 'alice', [], []),
    ('bob=d/alice', 'bob', 'alice', [], []),
    ('bob=D/alice', 'bob', 'alice', [], []),
    ('bob=x/alice', 'bob', 'alice', [], []),
    ('bob=t/alice', 'bob', 'alice', [], []),
    ('bob=X/alice', 'bob', 'alice', [], []),
    ('bob=U/alice', 'bob', 'alice', ['ALL'], []),
    ('bob=C/alice', 'bob', 'alice', [], []),
    ('bob=c/alice', 'bob', 'alice', [], []),
    ('bob=T/alice', 'bob', 'alice', [], []),

    ('bob=a*/alice', 'bob', 'alice', [], []),
    ('bob=r*/alice', 'bob', 'alice', [], []),
    ('bob=w*/alice', 'bob', 'alice', [], []),
    ('bob=d*/alice', 'bob', 'alice', [], []),
    ('bob=D*/alice', 'bob', 'alice', [], []),
    ('bob=x*/alice', 'bob', 'alice', [], []),
    ('bob=t*/alice', 'bob', 'alice', [], []),
    ('bob=X*/alice', 'bob', 'alice', [], []),
    ('bob=U*/alice', 'bob', 'alice', [], ['ALL']),
    ('bob=C*/alice', 'bob', 'alice', [], []),
    ('bob=c*/alice', 'bob', 'alice', [], []),
    ('bob=T*/alice', 'bob', 'alice', [], []),
]

parse_schema_data = [
    ('alice=CU/alice', 'alice', 'alice', ['ALL'], []),
    ('alice=C*U*/alice', 'alice', 'alice', [], ['ALL']),
    ('bob=CU/alice', 'bob', 'alice', ['ALL'], []),
    ('bob=C/alice', 'bob', 'alice', ['CREATE'], []),

    ('bob=a/alice', 'bob', 'alice', [], []),
    ('bob=r/alice', 'bob', 'alice', [], []),
    ('bob=w/alice', 'bob', 'alice', [], []),
    ('bob=d/alice', 'bob', 'alice', [], []),
    ('bob=D/alice', 'bob', 'alice', [], []),
    ('bob=x/alice', 'bob', 'alice', [], []),
    ('bob=t/alice', 'bob', 'alice', [], []),
    ('bob=X/alice', 'bob', 'alice', [], []),
    ('bob=U/alice', 'bob', 'alice', ['USAGE'], []),
    ('bob=C/alice', 'bob', 'alice', ['CREATE'], []),
    ('bob=c/alice', 'bob', 'alice', [], []),
    ('bob=T/alice', 'bob', 'alice', [], []),

    ('bob=a*/alice', 'bob', 'alice', [], []),
    ('bob=r*/alice', 'bob', 'alice', [], []),
    ('bob=w*/alice', 'bob', 'alice', [], []),
    ('bob=d*/alice', 'bob', 'alice', [], []),
    ('bob=D*/alice', 'bob', 'alice', [], []),
    ('bob=x*/alice', 'bob', 'alice', [], []),
    ('bob=t*/alice', 'bob', 'alice', [], []),
    ('bob=X*/alice', 'bob', 'alice', [], []),
    ('bob=U*/alice', 'bob', 'alice', [], ['USAGE']),
    ('bob=C*/alice', 'bob', 'alice', [], ['CREATE']),
    ('bob=c*/alice', 'bob', 'alice', [], []),
    ('bob=T*/alice', 'bob', 'alice', [], []),
]

parse_database_data = [
    ('alice=CcT/alice', 'alice', 'alice', ['ALL'], []),
    ('alice=C*c*T*/alice', 'alice', 'alice', [], ['ALL']),
    ('bob=CcT/alice', 'bob', 'alice', ['ALL'], []),
    ('bob=Cc/alice', 'bob', 'alice', ['CREATE', 'CONNECT'], []),

    ('bob=a/alice', 'bob', 'alice', [], []),
    ('bob=r/alice', 'bob', 'alice', [], []),
    ('bob=w/alice', 'bob', 'alice', [], []),
    ('bob=d/alice', 'bob', 'alice', [], []),
    ('bob=D/alice', 'bob', 'alice', [], []),
    ('bob=x/alice', 'bob', 'alice', [], []),
    ('bob=t/alice', 'bob', 'alice', [], []),
    ('bob=X/alice', 'bob', 'alice', [], []),
    ('bob=U/alice', 'bob', 'alice', [], []),
    ('bob=C/alice', 'bob', 'alice', ['CREATE'], []),
    ('bob=c/alice', 'bob', 'alice', ['CONNECT'], []),
    ('bob=T/alice', 'bob', 'alice', ['TEMPORARY'], []),

    ('bob=a*/alice', 'bob', 'alice', [], []),
    ('bob=r*/alice', 'bob', 'alice', [], []),
    ('bob=w*/alice', 'bob', 'alice', [], []),
    ('bob=d*/alice', 'bob', 'alice', [], []),
    ('bob=D*/alice', 'bob', 'alice', [], []),
    ('bob=x*/alice', 'bob', 'alice', [], []),
    ('bob=t*/alice', 'bob', 'alice', [], []),
    ('bob=X*/alice', 'bob', 'alice', [], []),
    ('bob=U*/alice', 'bob', 'alice', [], []),
    ('bob=C*/alice', 'bob', 'alice', [], ['CREATE']),
    ('bob=c*/alice', 'bob', 'alice', [], ['CONNECT']),
    ('bob=T*/alice', 'bob', 'alice', [], ['TEMPORARY']),
]

parse_tablespace_data = [
    ('alice=C/alice', 'alice', 'alice', ['ALL'], []),
    ('alice=C*/alice', 'alice', 'alice', [], ['ALL']),
    ('bob=C/alice', 'bob', 'alice', ['ALL'], []),

    ('bob=a/alice', 'bob', 'alice', [], []),
    ('bob=r/alice', 'bob', 'alice', [], []),
    ('bob=w/alice', 'bob', 'alice', [], []),
    ('bob=d/alice', 'bob', 'alice', [], []),
    ('bob=D/alice', 'bob', 'alice', [], []),
    ('bob=x/alice', 'bob', 'alice', [], []),
    ('bob=t/alice', 'bob', 'alice', [], []),
    ('bob=X/alice', 'bob', 'alice', [], []),
    ('bob=U/alice', 'bob', 'alice', [], []),
    ('bob=C/alice', 'bob', 'alice', ['ALL'], []),
    ('bob=c/alice', 'bob', 'alice', [], []),
    ('bob=T/alice', 'bob', 'alice', [], []),

    ('bob=a*/alice', 'bob', 'alice', [], []),
    ('bob=r*/alice', 'bob', 'alice', [], []),
    ('bob=w*/alice', 'bob', 'alice', [], []),
    ('bob=d*/alice', 'bob', 'alice', [], []),
    ('bob=D*/alice', 'bob', 'alice', [], []),
    ('bob=x*/alice', 'bob', 'alice', [], []),
    ('bob=t*/alice', 'bob', 'alice', [], []),
    ('bob=X*/alice', 'bob', 'alice', [], []),
    ('bob=U*/alice', 'bob', 'alice', [], []),
    ('bob=C*/alice', 'bob', 'alice', [], ['ALL']),
    ('bob=c*/alice', 'bob', 'alice', [], []),
    ('bob=T*/alice', 'bob', 'alice', [], []),
]

parse_type_data = parse_language_data
parse_fdw_data = parse_language_data
parse_foreign_server_data = parse_language_data

parse_foreign_table_data = [
    ('alice=r/alice', 'alice', 'alice', ['ALL'], []),
    ('alice=r*/alice', 'alice', 'alice', [], ['ALL']),
    ('bob=r/alice', 'bob', 'alice', ['ALL'], []),

    ('bob=a/alice', 'bob', 'alice', [], []),
    ('bob=r/alice', 'bob', 'alice', ['ALL'], []),
    ('bob=w/alice', 'bob', 'alice', [], []),
    ('bob=d/alice', 'bob', 'alice', [], []),
    ('bob=D/alice', 'bob', 'alice', [], []),
    ('bob=x/alice', 'bob', 'alice', [], []),
    ('bob=t/alice', 'bob', 'alice', [], []),
    ('bob=X/alice', 'bob', 'alice', [], []),
    ('bob=U/alice', 'bob', 'alice', [], []),
    ('bob=C/alice', 'bob', 'alice', [], []),
    ('bob=c/alice', 'bob', 'alice', [], []),
    ('bob=T/alice', 'bob', 'alice', [], []),

    ('bob=a*/alice', 'bob', 'alice', [], []),
    ('bob=r*/alice', 'bob', 'alice', [], ['ALL']),
    ('bob=w*/alice', 'bob', 'alice', [], []),
    ('bob=d*/alice', 'bob', 'alice', [], []),
    ('bob=D*/alice', 'bob', 'alice', [], []),
    ('bob=x*/alice', 'bob', 'alice', [], []),
    ('bob=t*/alice', 'bob', 'alice', [], []),
    ('bob=X*/alice', 'bob', 'alice', [], []),
    ('bob=U*/alice', 'bob', 'alice', [], []),
    ('bob=C*/alice', 'bob', 'alice', [], []),
    ('bob=c*/alice', 'bob', 'alice', [], []),
    ('bob=T*/alice', 'bob', 'alice', [], []),
]

parse_lob_data = [
    ('alice=rw/alice', 'alice', 'alice', ['ALL'], []),
    ('alice=r*w*/alice', 'alice', 'alice', [], ['ALL']),
    ('bob=rw/alice', 'bob', 'alice', ['ALL'], []),
    ('bob=r/alice', 'bob', 'alice', ['SELECT'], []),

    ('bob=a/alice', 'bob', 'alice', [], []),
    ('bob=r/alice', 'bob', 'alice', ['SELECT'], []),
    ('bob=w/alice', 'bob', 'alice', ['UPDATE'], []),
    ('bob=d/alice', 'bob', 'alice', [], []),
    ('bob=D/alice', 'bob', 'alice', [], []),
    ('bob=x/alice', 'bob', 'alice', [], []),
    ('bob=t/alice', 'bob', 'alice', [], []),
    ('bob=X/alice', 'bob', 'alice', [], []),
    ('bob=U/alice', 'bob', 'alice', [], []),
    ('bob=C/alice', 'bob', 'alice', [], []),
    ('bob=c/alice', 'bob', 'alice', [], []),
    ('bob=T/alice', 'bob', 'alice', [], []),

    ('bob=a*/alice', 'bob', 'alice', [], []),
    ('bob=r*/alice', 'bob', 'alice', [], ['SELECT']),
    ('bob=w*/alice', 'bob', 'alice', [], ['UPDATE']),
    ('bob=d*/alice', 'bob', 'alice', [], []),
    ('bob=D*/alice', 'bob', 'alice', [], []),
    ('bob=x*/alice', 'bob', 'alice', [], []),
    ('bob=t*/alice', 'bob', 'alice', [], []),
    ('bob=X*/alice', 'bob', 'alice', [], []),
    ('bob=U*/alice', 'bob', 'alice', [], []),
    ('bob=C*/alice', 'bob', 'alice', [], []),
    ('bob=c*/alice', 'bob', 'alice', [], []),
    ('bob=T*/alice', 'bob', 'alice', [], []),
]

parse_col_data = [
    ('alice=rwax/alice', 'alice', 'alice', ['ALL (id)'], []),
    ('alice=r*w*a*x*/alice', 'alice', 'alice', [], ['ALL (id)']),
    ('bob=rwax/alice', 'bob', 'alice', ['ALL (id)'], []),
    ('bob=rwa/alice', 'bob', 'alice', ['SELECT (id)', 'UPDATE (id)', 'INSERT (id)'], []),

    ('bob=a/alice', 'bob', 'alice', ['INSERT (id)'], []),
    ('bob=r/alice', 'bob', 'alice', ['SELECT (id)'], []),
    ('bob=w/alice', 'bob', 'alice', ['UPDATE (id)'], []),
    ('bob=d/alice', 'bob', 'alice', [], []),
    ('bob=D/alice', 'bob', 'alice', [], []),
    ('bob=x/alice', 'bob', 'alice', ['REFERENCES (id)'], []),
    ('bob=t/alice', 'bob', 'alice', [], []),
    ('bob=X/alice', 'bob', 'alice', [], []),
    ('bob=U/alice', 'bob', 'alice', [], []),
    ('bob=C/alice', 'bob', 'alice', [], []),
    ('bob=c/alice', 'bob', 'alice', [], []),
    ('bob=T/alice', 'bob', 'alice', [], []),

    ('bob=a*/alice', 'bob', 'alice', [], ['INSERT (id)']),
    ('bob=r*/alice', 'bob', 'alice', [], ['SELECT (id)']),
    ('bob=w*/alice', 'bob', 'alice', [], ['UPDATE (id)']),
    ('bob=d*/alice', 'bob', 'alice', [], []),
    ('bob=D*/alice', 'bob', 'alice', [], []),
    ('bob=x*/alice', 'bob', 'alice', [], ['REFERENCES (id)']),
    ('bob=t*/alice', 'bob', 'alice', [], []),
    ('bob=X*/alice', 'bob', 'alice', [], []),
    ('bob=U*/alice', 'bob', 'alice', [], []),
    ('bob=C*/alice', 'bob', 'alice', [], []),
    ('bob=c*/alice', 'bob', 'alice', [], []),
    ('bob=T*/alice', 'bob', 'alice', [], []),
]


@pytest.mark.parametrize('acl, grantee, grantor, privs, privswgo', parse_data)
def test_parse(acl, grantee, grantor, privs, privswgo):
    assert parse_acl_item(acl) == Privileges(grantee, grantor, privs, privswgo)


def test_parse_acl():
    assert parse_acl(['ali=a/ali', 'bob=a/ali']) == [
        Privileges(grantee='ali', grantor='ali', privs=['INSERT'], privswgo=[]),
        Privileges(grantee='bob', grantor='ali', privs=['INSERT'], privswgo=[])
    ]


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_table_data)
def test_parse_table(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.TABLE)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_sequence_data)
def test_parse_sequence(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.SEQUENCE)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_function_data)
def test_parse_function(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.FUNCTION)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_language_data)
def test_parse_language(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.LANGUAGE)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_schema_data)
def test_parse_schema(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.SCHEMA)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_database_data)
def test_parse_database(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.DATABASE)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_tablespace_data)
def test_parse_tablespace(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.TABLESPACE)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_type_data)
def test_parse_type(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.TYPE)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_fdw_data)
def test_parse_fdw(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.FOREIGN_DATA_WRAPPER)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_foreign_server_data)
def test_parse_foreign_server_data(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.FOREIGN_SERVER)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_foreign_table_data)
def test_parse_foreign_table_data(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.FOREIGN_TABLE)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_lob_data)
def test_parse_lob_data(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.LARGE_OBJECT)
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize(
    'acl, grantee, grantor, privs, privswgo', parse_col_data)
def test_parse_col_data(acl, grantee, grantor, privs, privswgo):
    parsed = parse_acl_item(acl, PgObjectType.TABLE, 'id')
    assert parsed == Privileges(grantee, grantor, privs, privswgo)


@pytest.mark.parametrize('acl', [
    '"bob=a/alice',
    'bo"b=a/alice',
    '"bob""=a/alice',
    '"=a/alice',
    'bob=a/"alice',
    'bob=a/al"ice',
    'bob=a/"alice""',
    'bob=a/"',
])
def test_parse_invalid_quote(acl):
    with pytest.raises(ValueError) as exc_info:
        parse_acl_item(acl)

    assert 'quote' in exc_info.value.args[0]


def test_parse_unknown_type():
    with pytest.raises(ValueError) as exc_info:
        # noinspection PyTypeChecker
        parse_acl_item('bob=a/alice', 'bad type')

    assert 'Unknown type' in exc_info.value.args[0]
