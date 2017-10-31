import pytest

from pg_grant import NoSuchObjectError
from pg_grant.query import get_all_language_acls, get_language_acl


expected_acls = {
    # sql has default privileges, so None is returned.
    'sql': None,
    # postgres is owner, alice was granted usage
    'plpgsql': ['postgres=U/postgres', 'alice=U/postgres'],
}


@pytest.mark.parametrize('name, acls', expected_acls.items())
def test_get_language_acl(connection, name, acls):
    """Find visible languages matching ``name``."""
    language = get_language_acl(connection, name)
    assert language.acl == acls


def test_get_all_language_acls(connection):
    """Get all languages in all schemas."""
    languages = get_all_language_acls(connection)

    tested = 0

    for language in languages:
        if language.name not in expected_acls:
            continue

        assert language.acl == expected_acls[language.name]
        tested += 1

    assert tested == len(expected_acls)


def test_no_such_object(connection):
    with pytest.raises(NoSuchObjectError):
        get_language_acl(connection, 'eggs')
