# Change Log

## [Unreleased][unreleased]
### Added
- `parse_acl` function to call `parse_acl_item` on each item in a list.
- Documentation on `parse_acl_item` about ensuring `subname` is a valid
  identifier if it is to be executed.

### Changed
- Renamed singular functions like `get_table_acls` to `get_table_acl`.
- `get_all_table_acls` and `get_table_acl` also return views, materialized
  views, partitioned tables (PostgreSQL 10+), and foreign tables.
- `grant` and `revoke` will quote the subname in privileges by default, to
  ensure it is a valid identifier. Use `quote_subname=False` to disable.

## [0.2.0.post0] - 2017-10-24

Minor packaging changes.

## [0.2.0] - 2017-10-24

First release.

[unreleased]: https://github.com/python-astrodynamics/spacetrack/compare/0.2.0.post0...HEAD
[0.2.0.post0]: https://github.com/RazerM/pg_grant/compare/38e53889bf9923b63d79805dc050dcd26a40d518...0.2.0.post0
[0.2.0]: https://github.com/RazerM/pg_grant/compare/38e53889bf9923b63d79805dc050dcd26a40d518...0.2.0
