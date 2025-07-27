PYTHON_TYPES_TO_SQL_NAMES = {
    bool: "INTEGER",
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bytes: "BLOB"
}

class ConversionMaster:
    """Converts python types to SQL types."""

    @staticmethod
    def dump[T](value: ..., base: type[T] = None) -> T:
        return value

    @staticmethod
    def load[T](value: ..., base: type[T]) -> T:
        return value

    @staticmethod
    def sql_types() -> tuple[type, ...]:
        """Return python types."""
        return tuple(PYTHON_TYPES_TO_SQL_NAMES.keys())

    @staticmethod
    def sql_name[T](base: type[T]) -> str:
        """Return the corresponding SQL type for the given python type."""
        return PYTHON_TYPES_TO_SQL_NAMES[base]

sql = ConversionMaster