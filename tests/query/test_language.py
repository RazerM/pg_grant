import pytest

from pg_grant.query import get_all_language_acls, get_language_acls


expected_acls = {
    # sql has default privileges, so None is returned.
    'sql': None,
    # postgres is owner, alice was granted usage
    'plpgsql': ['postgres=U/postgres', 'alice=U/postgres'],
}


@pytest.mark.parametrize('name, acls', expected_acls.items())
def test_get_language_acls(connection, name, acls):
    """Find visible languages matching ``name``."""
    language = get_language_acls(connection, name)
    assert language.acl == acls


def test_get_all_language_acls(connection):
    """Get all languages in all schemas."""
    languages = get_all_language_acls(connection)

    for language in languages:
        if language.name not in expected_acls:
            continue

        assert language.acl == expected_acls[language.name]
