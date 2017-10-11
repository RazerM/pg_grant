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
