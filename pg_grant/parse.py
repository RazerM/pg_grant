from typing import List, Optional, Sequence

from .types import Privileges, PgObjectType


def _get_acl_username(acl):
    """Port of ``copyAclUserName`` from ``dumputils.c``"""
    i = 0
    output = ''

    while i < len(acl) and acl[i] != '=':
        # If user name isn't quoted, then just add it to the output buffer
        if acl[i] != '"':
            output += acl[i]
            i += 1
        else:
            # Otherwise, it's a quoted username
            i += 1

            if i == len(acl):
                raise ValueError('ACL syntax error: unterminated quote.')

            # Loop until we come across an unescaped quote
            while not (acl[i] == '"' and acl[i + 1:i + 2] != '"'):
                # Quoting convention is to escape " as "".
                if acl[i] == '"' and acl[i + 1:i + 2] == '"':
                    i += 1

                output += acl[i]
                i += 1

                if i == len(acl):
                    raise ValueError('ACL syntax error: unterminated quote.')

            i += 1

    return i, output


def get_default_privileges(type: PgObjectType, owner: str) -> List[Privileges]:
    """Return a list of :class:`~pg_grant.types.Privileges` objects matching the
    default privileges for that type.

    This can be called when the ACL item from PostgreSQL is NULL to determine
    the implicit access privileges.

    .. seealso:: https://www.postgresql.org/docs/10/static/sql-grant.html
    """

    # "the owner has all privileges by default"
    # "PostgreSQL treats the owner's privileges as having been granted by the
    # owner to themselves"
    priv_list = [Privileges(grantee=owner, grantor=owner, privs=['ALL'])]

    public_privs = None

    # "PostgreSQL grants default privileges on some types of objects to PUBLIC.
    # No privileges are granted to PUBLIC by default on tables, columns,
    # schemas or tablespaces. For other types, the default privileges granted
    # to PUBLIC are as follows: CONNECT and CREATE TEMP TABLE for databases;
    # EXECUTE privilege for functions; and USAGE privilege for languages."
    if type is PgObjectType.DATABASE:
        public_privs = ['CONNECT', 'TEMPORARY']
    elif type is PgObjectType.FUNCTION:
        public_privs = ['EXECUTE']
    elif type is PgObjectType.LANGUAGE:
        public_privs = ['USAGE']
    elif type is PgObjectType.TYPE:
        # Seems like there's a documentation bug, and that types get USAGE by
        # default.
        # https://stackoverflow.com/questions/46656644
        public_privs = ['USAGE']

    if public_privs:
        priv_list.append(
            Privileges(grantee='PUBLIC', grantor=owner, privs=public_privs))

    return priv_list


def parse_acl(
    acl: Sequence[str],
    type: Optional[PgObjectType] = None,
    subname: Optional[str] = None,
) -> List[Privileges]:
    """

    Parameters:
        acl: ACL, e.g. ``['alice=arwdDxt/alice', 'bob=arwdDxt/alice']``
        type: Optional. If passed, all privileges may be reduced to ``['ALL']``.
        subname: Optional, e.g. for column privileges.

    Returns:
        List of :class:`~.types.Privileges`.

    .. seealso::

        This is a simple wrapper; :func:`.parse_acl_item` is called for each
        item in `acl`.
    """
    return [parse_acl_item(i, type, subname) for i in acl]


def parse_acl_item(
    acl_item: str,
    type: Optional[PgObjectType] = None,
    subname: Optional[str] = None,
) -> Privileges:
    """Port of ``parseAclItem`` from `dumputils.c`_

    Parameters:
        acl_item: ACL item, e.g. ``'alice=arwdDxt/bob'``
        type: Optional. If passed, all privileges may be reduced to ``['ALL']``.
        subname: Optional, e.g. for column privileges. Must be output from
                 :func:`psycopg2.extensions.quote_ident` or similar.

    .. warning::

        If the ``privs`` or ``privswgo`` attributes of the returned object will
        be used to construct an SQL statement, `subname` **must be a valid
        identifier** (e.g. by calling :func:`psycopg2.extensions.quote_ident`)
        in order to prevent SQL injection attacks.

        :func:`~pg_grant.sql.grant` and :func:`~pg_grant.sql.revoke` are not
        vulnerable, because those functions quote the embedded identifier:

        .. code-block:: python

            >>> from pg_grant import PgObjectType, parse_acl_item
            >>> from pg_grant.sql import grant
            >>> privs = parse_acl_item('alice=r/bob', subname='user')
            >>> privs.privs
            ['SELECT (user)']
            >>> str(grant(privs.privs, PgObjectType.TABLE, 'tbl1', 'alice'))
           'GRANT SELECT ("user") ON TABLE tbl1 TO alice'

        Note that ``"user"`` was quoted by :func:`~pg_grant.sql.grant`.

        In other cases, make sure to quote `subname`:

        .. code-block:: python

            >>> import psycopg2
            >>> from psycopg2.extensions import quote_ident
            >>> conn = psycopg2.connect(...)
            >>> parse_acl_item('alice=r/bob', subname=quote_ident('user', conn))
            >>> privs.privs
            ['SELECT ("user")']

    Returns:
        :class:`~.types.Privileges`
    """
    eq_pos, grantee = _get_acl_username(acl_item)
    assert acl_item[eq_pos] == '='

    if grantee == '':
        grantee = 'PUBLIC'

    slash_pos = acl_item.index('/', eq_pos)
    _, grantor = _get_acl_username(acl_item[slash_pos + 1:])

    privs = []
    privs_with_grant_option = []

    all_with_grant_option = all_without_grant_option = True

    priv = acl_item[eq_pos + 1:slash_pos]

    def convert_priv(code, keyword):
        nonlocal all_with_grant_option, all_without_grant_option

        pos = priv.find(code)
        if pos >= 0:
            if priv[pos + 1:pos + 2] == '*':
                s = keyword
                if subname is not None:
                    s += ' ({})'.format(subname)

                privs_with_grant_option.append(s)
                all_without_grant_option = False
            else:
                s = keyword
                if subname is not None:
                    s += ' ({})'.format(subname)

                privs.append(s)
                all_with_grant_option = False
        else:
            all_with_grant_option = all_without_grant_option = False

    if type is None:
        convert_priv('r', 'SELECT')
        convert_priv('w', 'UPDATE')
        convert_priv('a', 'INSERT')
        convert_priv('d', 'DELETE')
        convert_priv('D', 'TRUNCATE')
        convert_priv('x', 'REFERENCES')
        convert_priv('t', 'TRIGGER')
        convert_priv('X', 'EXECUTE')
        convert_priv('U', 'USAGE')
        convert_priv('C', 'CREATE')
        convert_priv('c', 'CONNECT')
        convert_priv('T', 'TEMPORARY')

        # Don't think anything can have all of them, but set all to False
        # since we don't know type.
        all_with_grant_option = all_without_grant_option = False
    elif type in {PgObjectType.TABLE, PgObjectType.SEQUENCE}:
        convert_priv('r', 'SELECT')
        convert_priv('w', 'UPDATE')

        if type is PgObjectType.SEQUENCE:
            convert_priv('U', 'USAGE')
        else:
            convert_priv('a', 'INSERT')
            convert_priv('x', 'REFERENCES')

            if subname is None:
                convert_priv('d', 'DELETE')
                convert_priv('t', 'TRIGGER')
                convert_priv('D', 'TRUNCATE')

    elif type is PgObjectType.FUNCTION:
        convert_priv('X', 'EXECUTE')
    elif type is PgObjectType.LANGUAGE:
        convert_priv('U', 'USAGE')
    elif type is PgObjectType.SCHEMA:
        convert_priv('C', 'CREATE')
        convert_priv('U', 'USAGE')
    elif type is PgObjectType.DATABASE:
        convert_priv('C', 'CREATE')
        convert_priv('c', 'CONNECT')
        convert_priv('T', 'TEMPORARY')
    elif type is PgObjectType.TABLESPACE:
        convert_priv('C', 'CREATE')
    elif type is PgObjectType.TYPE:
        convert_priv('U', 'USAGE')
    elif type is PgObjectType.FOREIGN_DATA_WRAPPER:
        convert_priv('U', 'USAGE')
    elif type is PgObjectType.FOREIGN_SERVER:
        convert_priv('U', 'USAGE')
    elif type is PgObjectType.FOREIGN_TABLE:
        convert_priv('r', 'SELECT')
    elif type is PgObjectType.LARGE_OBJECT:
        convert_priv('r', 'SELECT')
        convert_priv('w', 'UPDATE')
    else:
        raise ValueError('Unknown type: {}'.format(type))

    if all_with_grant_option:
        privs = []
        privs_with_grant_option = []
        s = 'ALL'

        if subname is not None:
            s += ' ({})'.format(subname)

        privs_with_grant_option.append(s)
    elif all_without_grant_option:
        privs = []
        privs_with_grant_option = []
        s = 'ALL'

        if subname is not None:
            s += ' ({})'.format(subname)

        privs.append(s)

    return Privileges(grantee, grantor, privs, privs_with_grant_option)
