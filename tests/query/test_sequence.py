import pytest

from pg_grant import NoSuchObjectError
from pg_grant.query import get_all_sequence_acls, get_sequence_acl


expected_acls = {
    'public': {
        # seq1 has default privileges, so None is returned.
        'seq1': None,
        # alice is owner, bob was granted all
        'seq2': ['alice=rwU/alice', 'bob=rwU/alice'],
    },
    'schema1': {
        'seq3': None,
    }
}


@pytest.mark.parametrize('name, acls', expected_acls['public'].items())
def test_get_sequence_acl_visible(connection, name, acls):
    """Find visible (i.e. in search path) sequences matching ``name``."""
    sequence = get_sequence_acl(connection, name)
    assert sequence.acl == acls


@pytest.mark.parametrize('schema, name, acls', [
    (schema, seq, acl)
    for schema, d in expected_acls.items()
    for seq, acl in d.items()
])
def test_get_sequence_acl_schema(connection, schema, name, acls):
    """Find sequences  from ``schema`` matching ``name``."""
    sequence = get_sequence_acl(connection, name, schema)
    assert sequence.acl == acls


def test_get_all_sequence_acls(connection):
    """Get all sequences in all schemas."""
    sequences = get_all_sequence_acls(connection)
    assert {x.schema for x in sequences} == {'public', 'schema1'}

    tested = 0

    for sequence in sequences:
        if sequence.schema not in expected_acls:
            continue

        if sequence.name not in expected_acls[sequence.schema]:
            continue

        assert sequence.acl == expected_acls[sequence.schema][sequence.name]
        tested += 1

    assert tested == sum(len(v) for v in expected_acls.values())


def test_no_such_object(connection):
    with pytest.raises(NoSuchObjectError):
        get_sequence_acl(connection, 'seq3')
