import sys
from typing import Any, List, Tuple, Type, Union

from sqlalchemy import Executable
from sqlalchemy import Sequence as SequenceType
from sqlalchemy import TableClause
from sqlalchemy.orm import Mapper

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias


ExecutableType: TypeAlias = Executable
TableTarget: TypeAlias = Union[
    TableClause,
    Type[Any],
    Mapper[Any],
]

AnyTarget: TypeAlias = Union[TableTarget, SequenceType, str]
ArgTypesInput: TypeAlias = Union[List[str], Tuple[str, ...]]

__all__ = (
    "AnyTarget",
    "ArgTypesInput",
    "ExecutableType",
    "TableTarget",
    "SequenceType",
)
