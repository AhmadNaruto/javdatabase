# sqliteshelve module
# https://github.com/devnull255/sqlite-shelve
import pickle, sqlite3
from collections import namedtuple

class SqliteShelve(object):
    __slots__ = "db"

    def __init__(self, dbpath):
        """Opens or creates an existing sqlite3_shelf"""

        self.db = sqlite3.connect(dbpath)
        # create shelf table if it doesn't already exist
        cursor = self.db.cursor()
        cursor.execute(
            "select * from sqlite_master where type = 'table' and tbl_name = 'shelf'"
        )
        rows = cursor.fetchall()
        if len(rows) == 0:
            cursor.execute(
                "create table data (id integer primary key autoincrement, key_str text, value_str text, unique(key_str))"
            )
        
        cursor.close()
    
    @staticmethod
    def to_object(obj, result:dict):
        return obj(*result.values())

    @staticmethod
    def create_object(result:dict):
        return namedtuple("Result", " ".join(result.keys()))

    def find(self, key):
        curr = self.db.cursor()
        dt = curr.execute(
            "select key_str, value_str from shelf where key_str like :key",
            {"key": f"%_%{key}%_%"},
        )
        result = dt.fetchall()
        curr.close()
        if not result or len(result) == 0:
            return None
        valres = []
        for res in result:
            rs = {"key": res[0]}
            rs.update(pickle.loads(res[1]))
            valres.append(rs)
        return valres

    def add(self, key, value):
        self.__setitem__(key, value)

    def remove(self, key):
        self.__delitem__(key)

    def edit(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        """Sets an entry for key to value using pickling"""
        pdata = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
        curr = self.db.cursor()
        curr.execute(
            "insert or replace into shelf (key_str,value_str) values (:key,:value)",
            {"key": key, "value": sqlite3.Binary(pdata)},
        )
        curr.close()

    def get(self, key, default_value=None):
        """Returns an entry for key"""
        curr = self.db.cursor()
        curr.execute("select value_str from shelf where key_str = :key", {"key": key})
        result = curr.fetchone()
        curr.close()
        if result:
            return pickle.loads(result[0])
        else:
            return default_value

    def __getitem__(self, key):
        """Returns an entry for key"""
        curr = self.db.cursor()
        curr.execute("select value_str from shelf where key_str = :key", {"key": key})
        result = curr.fetchone()
        curr.close()
        if result:
            return pickle.loads(result[0])
        else:
            raise (KeyError, "Key: %s does not exist." % key)

    def keys(self):
        """Returns list of keys"""
        curr = self.db.cursor()
        curr.execute("select key_str from shelf")
        keylist = [row[0] for row in curr]
        curr.close()
        return keylist

    def __contains__(self, key):
        """
        implements in operator
        if <key> in db
        """
        return key in self.keys()

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        """Returns number of entries in shelf"""
        return len(self.keys())

    def __delitem__(self, key):
        """Deletes an existing item."""
        curr = self.db.cursor()
        curr.execute("delete from shelf where key_str = '%s'" % key)
        curr.close()

    def save(self):
        """
        Closes database and commits changes
        """
        self.db.commit()

    def terminate(self):
        self.db.close()
