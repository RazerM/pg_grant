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
        from .sql import grant

        statements = []

        if self.privs:
            statements.append(
                grant(self.privs, type_, target, self.grantee, **kwargs))

        if self.privswgo:
            statements.append(grant(
                self.privswgo, type_, target, self.grantee, grant_option=True,
                **kwargs))

        return statements

    def as_revoke_statements(self, type_: PgObjectType, target, **kwargs):
        from .sql import revoke

        statements = []

        if self.privs:
            statements.append(
                revoke(self.privs, type_, target, self.grantee, **kwargs))

        if self.privswgo:
            statements.append(revoke(
                self.privswgo, type_, target, self.grantee, grant_option=True,
                **kwargs))

        return statements


@attr.s(slots=True)
class RelationInfo:
    """Holds object information and privileges as queried using the
    :mod:`.query` submodule."""
    #: Row identifier.
    oid = attr.ib()

    #: Name of the table, sequence, etc.
    name = attr.ib()

    #: Owner of the relation.
    owner = attr.ib()

    #: Access privileges (unparsed).
    acl = attr.ib()


@attr.s(slots=True)
class SchemaRelationInfo(RelationInfo):
    """Holds object information and privileges as queried using the
    :mod:`.query` submodule."""
    #: The name of the schema that contains this relation.
    schema = attr.ib()


@attr.s(slots=True)
class FunctionInfo(SchemaRelationInfo):
    """Holds object information and privileges as queried using the
    :mod:`.query` submodule."""
    #: Data types of the function arguments.
    arg_types = attr.ib()
