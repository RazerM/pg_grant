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
