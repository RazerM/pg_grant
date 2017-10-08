from enum import Enum

import attr


class ObjectType(Enum):
    TABLE = 1
    SEQUENCE = 2
    FUNCTION = 3
    LANGUAGE = 4
    SCHEMA = 5
    DATABASE = 6
    TABLESPACE = 7
    TYPE = 8
    FOREIGN_DATA_WRAPPER = 9
    FOREIGN_SERVER = 10
    FOREIGN_TABLE = 11
    LARGE_OBJECT = 12


@attr.s(slots=True)
class Privileges:
    grantee = attr.ib()
    grantor = attr.ib()
    privs = attr.ib(default=attr.Factory(list))
    privswgo = attr.ib(default=attr.Factory(list))
