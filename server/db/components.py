from dataclasses import dataclass
from db.conversion import sql
from abc import ABC, abstractmethod
from typing import ClassVar


type DataType = bool | int | float | str | bytes | None
type Payload = tuple[DataType, ...]

class BaseStatement(ABC):

    def __and__(self, other: "BaseStatement") -> "All":
        return All(_statements(self, other, All))

    def __or__(self, other: "BaseStatement") -> "Any":
        return Any(_statements(self, other, Any))

    def __invert__(self) -> "Not | BaseStatement":
        return self.statement if isinstance(self, Not) else Not(self)

    @abstractmethod
    def query(self, raw: bool = False) -> str:
        pass

    @abstractmethod
    def dump(self, raw: bool = False) -> Payload:
        pass


def _statements(s: "All | Any", other: "All | Any", base: type["All | Any"]) -> tuple["BaseStatement", ...]:
    values = list(s.statements) if isinstance(s, base) else [s]
    values.extend(other.statements if isinstance(other, base) else [other])
    return tuple(values)


@dataclass(eq=False, frozen=True)
class Operand:
    """Represents value in an query."""

    value: DataType
    field: bool = None
    base: type[DataType] = None

    def dump_value(self) -> DataType:
        return sql.dump(self.value, self.base)

    def query(self, raw: bool = False) -> str:
        """Generates the SQL representation of the operand."""
        if self.field:
            return self.value

        if not raw:
            return "?"

        data = self.dump_value()
        if isinstance(data, str):
            return repr(data)
        return str(data)

    def dump(self, raw: bool = False) -> Payload:

        if raw or self.field:
            return tuple()

        return (self.value,)

    @staticmethod
    def auto(val: "Operand | Field | DataType") -> "Operand":
        if isinstance(val, Operand):
            return val
        if isinstance(val, Field):
            return field(val)
        return value(val)

    def typed(self, base: type = None) -> "Operand":
        return Operand(self.value, self.field, self.base or base)

    def _operands(self, other) -> tuple["Operand", "Operand"]:
        other = Operand.auto(other)

        return self.typed(other.base), other

    def __eq__(self, other: "Operand | Field | DataType") -> "Equals":
        return Equals(*self._operands(other))

    def __ne__(self, other: "Operand | Field | DataType") -> "NotEquals":
        return NotEquals(*self._operands(other))

    def __lt__(self, other: "Operand | Field | DataType") -> "Smaller":
        return Smaller(*self._operands(other))

    def __gt__(self, other: "Operand | Field | DataType") -> "Bigger":
        return Bigger(*self._operands(other))

    def __le__(self, other: "Operand | Field | DataType") -> "SmallerEquals":
        return SmallerEquals(*self._operands(other))

    def __ge__(self, other: "Operand | Field | DataType") -> "BiggerEquals":
        return BiggerEquals(*self._operands(other))

@dataclass(frozen=True, eq=False, unsafe_hash=True)
class Field[T: DataType]:
    """Represents a database column."""

    name: str  # The column name
    base: type[T]  # The Python type of the column
    primary: bool = None  # Indicates if the column is a primary key.
    unique: bool = None  # Indicates if the column values must be unique.
    nullable: bool = None  # Indicates if the column can be NULL.

    def definition(self) -> str:
        constraints = []

        if self.primary:
            constraints.append("PRIMARY KEY")

        if self.unique:
            constraints.append("UNIQUE")

        if not self.nullable:
            constraints.append("NOT NULL")

        return f"{self.name} {sql.sql_name(self.base)} {' '.join(constraints)}".strip()

    def dump(self, data: T | None) -> DataType:
        is_field_nullable = self.nullable is True

        if data is None:
            if is_field_nullable:
                return None
            else:
                raise ValueError(f"Data {data} is not of type {self.base} (field '{self.name}' is not nullable)")

        if not isinstance(data, self.base):
            raise ValueError(f"Data {data} is not of type {self.base}")
        return data

    def load(self, data: DataType) -> T | None:
        if data is None and self.nullable:
            return None
        if not isinstance(data, self.base):
            try:
                return self.base(data)
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert {data} to {self.base}")
        return data

    def _operands(self, other) -> tuple["Operand", "Operand"]:
        return field(self), Operand.auto(other).typed(self.base)

    def __eq__(self, other: "Operand | Field | DataType") -> BaseStatement:
        return Equals(*self._operands(other))

    def __ne__(self, other: "Operand | Field | DataType") -> BaseStatement:
        return NotEquals(*self._operands(other))

    def __lt__(self, other: "Operand | Field | DataType") -> BaseStatement:
        return Smaller(*self._operands(other))

    def __gt__(self, other: "Operand | Field | DataType") -> BaseStatement:
        return Bigger(*self._operands(other))

    def __le__(self, other: "Operand | Field | DataType") -> BaseStatement:
        return SmallerEquals(*self._operands(other))

    def __ge__(self, other: "Operand | Field | DataType") -> BaseStatement:
        return BiggerEquals(*self._operands(other))

def field(data: str | Field) -> Operand:
    if isinstance(data, str):
        return Operand(data, True)
    if isinstance(data, Field):
        return Operand(data.name, True, data.base)
    else:
        raise Exception("Invalid data.")

def value(data: DataType, base: type = None) -> Operand:
    return Operand(data, False, base)


@dataclass(frozen=True)
class All(BaseStatement):
    statements: tuple[BaseStatement, ...]

    def query(self, raw: bool = False) -> str:
        values = [f'({s.query(raw)})' for s in self.statements]

        return f" AND ".join(values)

    def dump(self, raw: bool = False) -> Payload:
        return _dump_statements(self, raw)


@dataclass(frozen=True)
class Any(BaseStatement):
    statements: tuple[BaseStatement, ...]

    def query(self, raw: bool = False) -> str:
        values = [f'({s.query(raw)})' for s in self.statements]

        return f" OR ".join(values)

    def dump(self, raw: bool = False) -> Payload:
        return _dump_statements(self, raw)


@dataclass(frozen=True)
class Not(BaseStatement):
    statement: BaseStatement

    def query(self, raw: bool = False) -> str:
        return f"NOT {self.statement.query(raw)}"

    def dump(self, raw: bool = False) -> Payload:
        return self.statement.dump(raw)


def _dump_statements(s: "All | Any", raw: bool = False) -> Payload:
    values = []

    for statement in s.statements:
        values.extend(statement.dump(raw))

    return tuple(values)


@dataclass(frozen=True)
class BaseOperation(BaseStatement, ABC):
    """Represents operation between 2 operands."""

    a: Operand
    b: Operand

    OPERATOR: ClassVar[str]

    def query(self, raw: bool = False) -> str:
        return f"{self.a.query(raw)} {self.OPERATOR} {self.b.query(raw)}"

    def dump(self, raw: bool = False) -> Payload:
        if raw or self.b.field:
            return tuple()
        return (self.b.value,)


class Equals(BaseOperation):
    OPERATOR: ClassVar[str] = "="

class NotEquals(BaseOperation):
    OPERATOR: ClassVar[str] = "!="

class BiggerEquals(BaseOperation):
    OPERATOR: ClassVar[str] = ">="

class SmallerEquals(BaseOperation):
    OPERATOR: ClassVar[str] = "<="

class Bigger(BaseOperation):
    OPERATOR: ClassVar[str] = ">"

class Smaller(BaseOperation):
    OPERATOR: ClassVar[str] = "<"

class Plus(BaseOperation):
    OPERATOR: ClassVar[str] = "+"

class Minus(BaseOperation):
    OPERATOR: ClassVar[str] = "-"

class Multiplication(BaseOperation):
    OPERATOR: ClassVar[str] = "*"

class Division(BaseOperation):
    OPERATOR: ClassVar[str] = "/"

if __name__ == '__main__':
    name = Field('name', str)
    s = (
            ((name == 'Ido') & ~(field('id') != 5)) |
            (field('name') == 'Adi')
    )
    print(s.query(raw=True))
    print(s.query(), s.dump())
