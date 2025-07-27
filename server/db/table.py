from dataclasses import dataclass
from typing import ClassVar, Iterable
from components import DataType, Field

type RawItem = tuple[DataType, ...]
type Item = dict[str | Field, DataType]


@dataclass(frozen=True)
class Table:
    name: str
    fields: tuple[Field, ...]

    def definition(self, exists_ok: bool = False) -> str:
        if_not_exists = "IF NOT EXISTS " if exists_ok else ""
        columns = ", ".join([field.definition() for field in self.fields])
        return f"CREATE TABLE {if_not_exists}{self.name} ({columns});"

    def names(self, fields: Iterable[str | Field] = None) -> Iterable[str]:

        if fields is None:
            fields = self.fields

        return [field.name if isinstance(field, Field) else field for field in fields]

    def sorted(self, fields: Iterable[str | Field] = None) -> tuple[str, ...]:

        input_names = self.names(fields)
        table_field_names = [field.name for field in self.fields]

        sorted_names = [name for name in table_field_names if name in input_names]
        return tuple(sorted_names)

    def item(self, data: Item | RawItem, fields: Iterable[str | Field] = None, load: bool = False) -> Item:
        field_map = {f.name: f for f in self.fields}

        if fields is not None:
            names_to_process = self.sorted(fields)
        elif isinstance(data, dict):
            input_data_string_keys = set()
            for key in data.keys():
                if isinstance(key, Field):
                    input_data_string_keys.add(key.name)
                elif isinstance(key, str):
                    input_data_string_keys.add(key)
            names_to_process = tuple(name for name in self.names(self.fields) if name in input_data_string_keys)
        else:
            names_to_process = self.sorted(self.fields)

        result_values_map = {}
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(key, Field):
                    result_values_map[key.name] = val
                else:
                    result_values_map[key] = val
        else:
            for i, name in enumerate(names_to_process):
                if i < len(data):
                    result_values_map[name] = data[i]

        result = {}
        for name in names_to_process:
            field = field_map[name]
            val = result_values_map.get(name)

            result[name] = (
                field.load(val) if load else field.dump(val)
            )
        return result
