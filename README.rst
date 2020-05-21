pg_grant
-------------

|PyPI Version| |Documentation| |Travis| |Coverage| |Python Version| |PostgreSQL Version| |License|

``pg_grant`` is a Python module for parsing, querying, and updating PostgreSQL
privileges.

Installation
~~~~~~~~~~~~

.. code:: bash

    $ pip install pg_grant[sqlalchemy]

Without the SQLAlchemy extra, ``pg_grant`` can only parse access privileges.

Example
~~~~~~~

.. code:: python

    >>> from pg_grant import parse_acl_item
    >>> parse_acl_item('bob=arw*/alice')
    Privileges(grantee='bob', grantor='alice', privs=['SELECT', 'INSERT'], privswgo=['UPDATE'])

    >>> from sqlalchemy import create_engine
    >>> from pg_grant.query import get_table_acl
    >>> engine = create_engine('postgresql://...')
    >>> get_table_acl(engine, 'table2')
    SchemaRelationInfo(oid=138067, name='table2', owner='alice', acl=['alice=arwdDxt/alice', 'bob=arwdDxt/alice'], schema='public')

    >>> from pg_grant import PgObjectType
    >>> from pg_grant.sql import revoke
    >>> stmt = revoke(['SELECT'], PgObjectType.TABLE, 'table2', 'bob')
    >>> str(stmt)
    'REVOKE SELECT ON TABLE table2 FROM bob'
    >>> engine.execute(stmt)

Authors
~~~~~~~
- Frazer McLean <frazer@frazermclean.co.uk>

Documentation
~~~~~~~~~~~~~

For in-depth information, `visit the
documentation <http://pg_grant.readthedocs.org/en/latest/>`__!

Development
~~~~~~~~~~~

pg_grant uses `semantic versioning <http://semver.org>`__

.. |Travis| image:: http://img.shields.io/travis/RazerM/pg_grant/master.svg?style=flat-square&label=Travis
    :target: https://travis-ci.org/RazerM/pg_grant
.. |PyPI Version| image:: http://img.shields.io/pypi/v/pg_grant.svg?style=flat-square&label=PyPI
    :target: https://pypi.python.org/pypi/pg_grant/
.. |Python Version| image:: https://img.shields.io/badge/Python-3-brightgreen.svg?style=flat-square
    :target: https://www.python.org/downloads/
.. |PostgreSQL Version| image:: https://img.shields.io/badge/PostgreSQL-9.5--12-blue.svg?style=flat-square
    :target: https://www.postgresql.org/
.. |License| image:: https://img.shields.io/github/license/RazerM/pg_grant.svg?style=flat-square
    :target: https://raw.githubusercontent.com/RazerM/pg_grant/master/LICENSE.txt
.. |Coverage| image:: https://img.shields.io/codecov/c/github/RazerM/pg_grant/master.svg?style=flat-square
    :target: https://codecov.io/github/RazerM/pg_grant?branch=master
.. |Documentation| image:: https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat-square
    :target: http://pg_grant.readthedocs.org/en/latest/
