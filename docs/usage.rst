*****
Usage
*****

Terminology
===========

Access Control List (ACL)
    pg_grant uses Access Control List, or ACL, to refer to a list of privileges
    in string form.

    .. code-block:: python

        acl = ['alice=arw/alice', 'bob=ar*/alice']

ACL item
   A single item in an Access Control List

    .. code-block:: python

        acl_item = 'alice=arw/alice'

Parsing
=======

Single ACL items can be parsed using :func:`~pg_grant.parse.parse_acl_item`:

.. code-block:: python

   >>> from pg_grant import parse_acl_item
   >>> parse_acl_item('bob=arw*/alice')
   Privileges(grantee='bob', grantor='alice', privs=['SELECT', 'INSERT'], privswgo=['UPDATE'])

Access Control Lists can be parsed using :func:`~.pg_grant.parse.parse_acl`:

.. code-block:: python

   >>> from pg_grant import parse_acl
   >>> parse_acl(['alice=a/alice', 'bob=a/alice'])
   [Privileges(grantee='alice', grantor='alice', privs=['INSERT'], privswgo=[]),
    Privileges(grantee='bob', grantor='alice', privs=['INSERT'], privswgo=[])]

Querying
========

The :mod:`pg_grant.query` submodule has functions for loading ACLs for many
types of database object. These functions use an SQLALchemy connection:

.. code-block:: python

    >>> from pg_grant import query as q
    >>> q.get_all_table_acls(engine, schema='public')
    [SchemaRelationInfo(oid=138067, name='table2', owner='alice', acl=['bob=arw/alice'], schema='public')
     ...]
    >>> q.get_table_acl(engine, 'table2')
    SchemaRelationInfo(oid=138067, name='table2', owner='alice', acl=['bob=arw/alice'], schema='public')

All of the functions return an object or list of objects with ``acl``
attributes that can be parsed with :func:`~pg_grant.parse.parse_acl`.

When an acl is ``None``, it means that default privileges apply to the object:

.. code-block:: python

    >>> from pg_grant import PgObjectType, get_default_privileges
    >>> from pg_grant import query as q
    >>> q.get_table_acl(engine, 'table2')
    SchemaRelationInfo(oid=138067, name='table2', owner='alice', acl=None, schema='public')
    >>> get_default_privileges(PgObjectType.TABLE, owner='alice')
    [Privileges(grantee='alice', grantor='alice', privs=['ALL'], privswgo=[])]
