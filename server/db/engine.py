import dataclasses
import sqlite3
from typing import Iterable, Self
from query import Query, Insert
from dataclasses import dataclass

@dataclass
class Engine:
    path: str = None
    conn: sqlite3.Connection | None = None

    def open(self, path: str = None) -> Self:
        self.path = self.path if path is None else path
        self.conn = sqlite3.connect(self.path)

        return self

    def cursor(self) -> sqlite3.Cursor:
        return self.conn.cursor()

    def execute[D](self, query: Query[D, ...], executor: sqlite3.Cursor = None, raw: bool = False) -> Iterable[D]:
        executor = self.conn if executor is None else executor
        caller = (
            executor.executemany if isinstance(query, Insert)
            else executor.execute
        )
        output = caller(query.query(raw), query.dump(raw))

        return query.process(output)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
        self.conn = None