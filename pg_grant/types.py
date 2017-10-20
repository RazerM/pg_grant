from enum import Enum

import attr


class PgObjectType(Enum):
    TABLE = 'TABLE'
    SEQUENCE = 'SEQUENCE'
    FUNCTION = 'FUNCTION'
    LANGUAGE = 'LANGUAGE'
    SCHEMA = 'SCHEMA'
    DATABASE = 'DATABASE'
    TABLESPACE = 'TABLESPACE'
    TYPE = 'TYPE'
    FOREIGN_DATA_WRAPPER = 'FOREIGN DATA WRAPPER'
    FOREIGN_SERVER = 'FOREIGN SERVER'
    FOREIGN_TABLE = 'FOREIGN TABLE'
    LARGE_OBJECT = 'LARGE OBJECT'


@attr.s(slots=True)
class Privileges:
    grantee = attr.ib()
    grantor = attr.ib()
    privs = attr.ib(default=attr.Factory(list))
    privswgo = attr.ib(default=attr.Factory(list))

    def as_grant_statements(self, type_: PgObjectType, target, **kwargs):
        from .sql import Grant

        statements = []

        if self.privs:
            statements.append(
                Grant(self.privs, type_, target, self.grantee, **kwargs))

        if self.privswgo:
            statements.append(Grant(
                self.privswgo, type_, target, self.grantee, grant_option=True,
                **kwargs))

        return statements

    def as_revoke_statements(self, type_: PgObjectType, target, **kwargs):
        from .sql import Revoke

        statements = []

        if self.privs:
            statements.append(
                Revoke(self.privs, type_, target, self.grantee, **kwargs))

        if self.privswgo:
            statements.append(Revoke(
                self.privswgo, type_, target, self.grantee, grant_option=True,
                **kwargs))

        return statements
