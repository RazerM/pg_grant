from enum import Enum

import attr


class PgObjectType(Enum):
    """PostgreSQL object type."""
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
    """Stores information from a parsed privilege string.

    .. seealso:: :func:`~.parse.parse_acl_item`
    """
    grantee = attr.ib()
    grantor = attr.ib()
    privs = attr.ib(factory=list)
    privswgo = attr.ib(factory=list)

    def as_grant_statements(self, type_: PgObjectType, target, **kwargs):
        """Return array of :func:`~.sql.grant` statements that can be executed
        to grant these privileges. Refer to the function documentation for the
        meaning of `target` and additional keyword arguments.

        .. note:: This requires installing with the ``sqlalchemy`` extra.
        """
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
        """Return array of :func:`~.sql.revoke` statements that can be executed
        to revoke these privileges. Refer to the function documentation for the
        meaning of `target` and additional keyword arguments.

        .. note::

            The statement for the `privswgo` privileges will revoke them
            fully, not only their grant options.

        .. note:: This requires installing with the ``sqlalchemy`` extra.
        """
        from .sql import revoke

        statements = []

        if self.privs:
            statements.append(
                revoke(self.privs, type_, target, self.grantee, **kwargs))

        if self.privswgo:
            statements.append(revoke(
                self.privswgo, type_, target, self.grantee, **kwargs))

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

    #: Access control list.
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


@attr.s(slots=True)
class ColumnInfo:
    """Holds object information and privileges as queried using the
    :mod:`.query` submodule."""
    #: Table identifier.
    table_oid = attr.ib()

    #: The name of the schema that contains the table.
    schema = attr.ib()

    #: Name of the table.
    table = attr.ib()

    #: Name of the column.
    column = attr.ib()

    #: Owner of the table.
    owner = attr.ib()

    #: Column access control list.
    acl = attr.ib()
