from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Iterable
from typing import Self
from components import Field, BaseStatement
from table import Table, RawItem, Item


class Query[D: RawItem, P: RawItem | Iterable[RawItem]](ABC):

    @abstractmethod
    def query(self, raw: bool = False) -> str:
        pass

    def process(self, output: Iterable[RawItem]) -> Iterable[D]:
        return output

    def dump(self, raw: bool = False) -> P:
        return ()


class StatementQuery(ABC):
    statement: BaseStatement

    def where(self, statement: BaseStatement) -> Self:
        self.statement = statement
        return self

    def dump_statement(self, raw: bool = False) -> RawItem:
        return (
        () if (self.statement is None) else
        self.statement.dump(raw)
        )


class FieldsQuery(ABC):
    fields: Iterable[str | Field] | None = None

    def all(self) -> Self:
        self.fields = None
        return self

    def each(self, fields: str | Field | Iterable[str | Field]) -> Self:
        self.fields = (fields if not isinstance(fields, (str, Field)) else (fields,))
        return self


@dataclass
class Create(Query[RawItem, RawItem]):
    table: Table
    exists_ok: bool = False

    def ignore(self) -> Self:
        self.exists_ok = True

        return self

    def fail(self) -> Self:
        self.exists_ok = False

        return self

    def adjust(self, exists_ok: bool) -> Self:
        self.exists_ok = exists_ok

        return self

    def query(self, raw: bool = False) -> str:
        return self.table.definition(self.exists_ok)

def test_create():
    id_field = Field("id", int, primary=True, unique=True)
    name_field = Field("name", str)
    table = Table("users", (id_field, name_field))
    create = Create(table).ignore()
    print(create.query())


@dataclass
class Select(Query[Item, RawItem], StatementQuery, FieldsQuery):
    table: Table
    fields: Iterable[str | Field | None] = None
    statement: BaseStatement = None

    def query(self, raw: bool = False) -> str:

        if raw:
            select_clause = "SELECT *"
        else:
            processed_fields = [field.name if isinstance(field, Field) else field for field in
                                (self.fields or self.table.fields)]
            select_clause = f"SELECT {', '.join(processed_fields)}"

        query = f"{select_clause} FROM {self.table.name}"

        if self.statement:
            query += f" WHERE {self.statement.query(raw)}"

        return query + ";"

    def process(self, output: Iterable[RawItem]) -> Iterable[Item]:
        for row in output:
            yield self.table.item(row, self.fields, load=True)

    def dump(self, raw: bool = False) -> RawItem:
        return self.dump_statement(raw)

def test_select():
    id_field = Field("id", int, primary=True)
    name_field = Field("name", str)
    table = Table("users", (id_field, name_field))
    select = Select(table).each(name_field).where(id_field == 1)
    print(select.query(), select.dump())


@dataclass
class Insert[T: Item | RawItem](Query[RawItem, Iterable[RawItem]], FieldsQuery):
    table: Table
    fields: Iterable[str | Field | None] = None
    data: Iterable[T] = None

    def query(self, raw: bool = False) -> str:
        insert_fields = self.fields if self.fields is not None else self.table.fields
        field_names = tuple(self.table.names(insert_fields))

        columns_clause = f" ({', '.join(field_names)})" if field_names else ""

        if raw:
            values_list = []
            if self.data:
                first_item = next(iter(self.data))
                dump_fields_for_item = self.fields if self.fields is not None else self.table.fields
                dumped_values = self.table.item(first_item, dump_fields_for_item, load=False).values()
                values_list = [repr(v) if isinstance(v, str) else str(v) for v in dumped_values]
            values_placeholders = f" ({', '.join(values_list)})" if values_list else " ()"
        else:
            num_placeholders = len(field_names)
            values_placeholders = f" ({', '.join(['?'] * num_placeholders)})"

        return f"INSERT INTO {self.table.name}{columns_clause} VALUES{values_placeholders};"

    def dump(self, raw: bool = False) -> Iterable[RawItem]:

        dump_fields = self.fields if self.fields is not None else self.table.fields

        for item in self.data:
            yield tuple(self.table.item(item, dump_fields, load=False).values())

    def values(self, items: Iterable[T]) -> Self:
        self.data = items

        return self

def test_insert():
    id_field = Field("id", int, primary=True)
    name_field = Field("name", str)
    table = Table("users", (id_field, name_field))
    insert = Insert(table).values([{"name": "a", id_field: 1}])
    print(insert.query(), list(insert.dump()))


@dataclass
class Update[T: Item | RawItem](Query[RawItem, RawItem], StatementQuery, FieldsQuery):
    table: Table
    data: T = None
    fields: Iterable[str | Field] | None = None
    statement: BaseStatement | None = None

    def query(self, raw: bool = False) -> str:
        if self.data is None:
            raise ValueError("Update data must be provided using .set() method.")

        # Pass self.fields directly. If self.fields is None, table.item will infer from self.data.
        # If self.fields is set (via .each()), table.item will use those fields.
        processed_data_dict = self.table.item(self.data, fields=self.fields, load=False)

        set_parts = []
        for field_name, value in processed_data_dict.items():
            if raw:
                if isinstance(value, str):
                    set_parts.append(f"{field_name} = {repr(value)}")
                else:
                    set_parts.append(f"{field_name} = {str(value)}")
            else:
                set_parts.append(f"{field_name} = ?")

        set_clause = ", ".join(set_parts)

        sql_query = f"UPDATE {self.table.name} SET {set_clause}"

        if self.statement:
            sql_query += f" WHERE {self.statement.query(raw)}"

        sql_query += ";"
        return sql_query

    def dump_values(self, raw: bool = False) -> RawItem:
        if raw:
            return ()
        if self.data is None:
            return ()

        # Pass self.fields directly. If self.fields is None, table.item will infer from self.data.
        processed_data_dict = self.table.item(self.data, fields=self.fields, load=False)

        return tuple(processed_data_dict.values())

    def dump(self, raw: bool = False) -> RawItem:
        return self.dump_values(raw) + self.dump_statement(raw)

    def set(self, item: T) -> Self:
        self.data = item
        return self

def test_update():
    id_field = Field("id", int, primary=True)
    name_field = Field("name", str)
    table = Table("users", (id_field, name_field))
    update = Update(table).set(({"name": "a"})).where(id_field == 1)
    print(update.query(), update.dump())


@dataclass
class Delete(Query[RawItem, RawItem], StatementQuery):
    table: Table
    statement: BaseStatement = None # Changed from Statement to BaseStatement for consistency

    def query(self, raw: bool = False) -> str:
        sql_query = f"DELETE FROM {self.table.name}"
        if self.statement:
            sql_query += f" WHERE {self.statement.query(raw)}"
        sql_query += ";"
        return sql_query

    def dump(self, raw: bool = False) -> RawItem:
        return self.dump_statement(raw)


@dataclass
class Drop(Query[RawItem, RawItem]):
    table: Table

    def query(self, raw: bool = False) -> str:
        return f"DROP TABLE {self.table.name};"

def test_delete_drop():
    id_field = Field("id", int, primary=True)
    name_field = Field("name", str)
    table = Table("users", (id_field, name_field))
    delete = Delete(table).where(id_field == 1)
    print(delete.query(), delete.dump())
    print(Drop(table).query())


if __name__ == '__main__':
    test_delete_drop()
