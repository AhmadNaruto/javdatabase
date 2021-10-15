from sqlite3 import Connection, connect
from collections import namedtuple
from os.path import exists


def object_factory(cursor, row):
    Row = namedtuple("result", [col[0] for col in cursor.description])
    return Row(*row)


class Database(object):
    def __init__(self, dbpath: str, wal: bool = False) -> None:
        self.db = connect(dbpath, isolation_level=None)
        if wal:
            self.db.execute("pragma journal_mode=wal")
        self.db.execute("pragma cache_size=1000")
        self.db.execute("pragma foreign_keys=1")
        self.db.row_factory = object_factory

    def build_table(self, sqlfile: str) -> None:
        if exists(sqlfile):
            with open(sqlfile) as sql:
                return self.db.executescript(sql.read())

        raise Exception(f"[No File] file : {sqlfile} not exists")

class Table(object):
    def __init__(self, tablename: str, con: Connection) -> None:
        self.cursor = con
        self.table = tablename

    def insert(self, data: dict = None, **kwargs) -> int:
        kwargs = data if data else kwargs
        return self.cursor.execute(
            f"insert into {self.table} \
            ({','.join(kwargs.keys())}) values \
            ({','.join([f':{n}' for n in kwargs.keys()])})",
            kwargs,
        ).lastrowid

    def delete(self, **data) -> None:
        self.cursor.execute(
            f"delete from {self.table} where {list(data.keys())[0]}=:{list(data.keys())[0]}",
            data
        )

    def _get(self, fields: list, cond: dict):
        return self.cursor.execute(
            f"select {','.join(fields)} from {self.table} where {list(cond.keys())[0]}=:{list(cond.keys())[0]}",
            cond,
        )

    def get_one(self, fields: list, **cond):
        return self._get(fields, cond).fetchone()

    def get_all(self, fields: list, **cond):
        return self._get(fields, cond).fetchall()
