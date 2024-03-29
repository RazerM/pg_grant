# Change Log

## [Unreleased][unreleased]

**This release supports SQLAlchemy 2.0 or later**

### Added

- `get_all_parameter_acls`
- `get_parameter_acl`
- `PgOjectType.DOMAIN`
- `PgOjectType.PARAMETER`

### Changed

- Python 3.8 or later is required.
- The following arguments for `grant` and `revoke` are now keyword-only:
  - `grant_option`
  - `schema`
  - `arg_types`
  - `quote_subname`
- The following arguments for `as_grant_statements` and `as_revoke_statements`
  are now keyword-only:
  - `schema`
  - `arg_types`
  - `quote_subname`
- The `type_` parameter for `as_grant_statements` and `as_revoke_statements` was
  renamed to `type`.
- Installing `pg-grant[sqlalchemy]` no longer installs psycopg2. Make sure you
  depend on a driver like `sqlalchemy[postgresql]` (psycopg2) or
  `sqlalchemy[postgresql_psycopg]` (psycopg 3).

### Removed

- `pg_grant.__version__`, use `importlib.metadata` instead.
- `pg_grant.__description__`, use `importlib.metadata` instead.
- `pg_grant.__license__`, use `importlib.metadata` instead.
- `pg_grant.__author__`, use `importlib.metadata` instead.
- `pg_grant.__email__`, use `importlib.metadata` instead.

## [0.4.0][]

**This release supports SQLAlchemy 1.4 and 2.0. The next release will require
SQLAlchemy 2.0 or later**

## Changed

- Python 3.6 or later is required.

## [0.3.3][]

**This release supports SQLAlchemy 1.3 and 1.4. The next release will require
SQLAlchemy 1.4 or later**

### Fixed

- ACLs for functions without any arguments (i.e. `arg_types=()`) could not be
  queried using `get_function_acl`.

## [0.3.2][] - 2020-05-21

### Fixed

- Type annotations for `parse_acl` and `parse_acl_item`.

## [0.3.1][] - 2018-01-17

### Fixed

- `pg_grant` can be installed with setuptools v38.0+, which requires
  `install_requires` in `setup.py` to be ordered.

## [0.3.0][] - 2017-10-31

### Added

- `parse_acl` function to call `parse_acl_item` on each item in a list.
- Documentation on `parse_acl_item` about ensuring `subname` is a valid
  identifier if it is to be executed.
- `get_all_column_acls` and `get_column_acls` to get column ACLs.

### Changed

- Renamed singular functions like `get_table_acls` to `get_table_acl`.
- `get_all_table_acls` and `get_table_acl` also return views, materialized
  views, partitioned tables (PostgreSQL 10+), and foreign tables.
- `grant` and `revoke` will quote the subname in privileges by default, to
  ensure it is a valid identifier. Use `quote_subname=False` to disable.
- `Privileges.as_revoke_statements` will revoke the privileges with grant
  options fully.
- `get_all_function_acls` and `get_function_acl` now return canonical type
  names, e.g. 'integer' instead of 'int4'. The `arg_types` parameter on
  `get_function_acl` also canonicalizes user input.

## [0.2.0.post0] - 2017-10-24

Minor packaging changes.

## [0.2.0] - 2017-10-24

First release.

[unreleased]: https://github.com/RazerM/pg_grant/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/RazerM/pg_grant/compare/v0.3.3...v0.4.0
[0.3.3]: https://github.com/RazerM/pg_grant/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/RazerM/pg_grant/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/RazerM/pg_grant/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/RazerM/pg_grant/compare/v0.2.0...v0.3.0
[0.2.0.post0]: https://github.com/RazerM/pg_grant/compare/v0.2.0...v0.2.0.post0
[0.2.0]: https://github.com/RazerM/pg_grant/compare/38e53889bf9923b63d79805dc050dcd26a40d518...v0.2.0
