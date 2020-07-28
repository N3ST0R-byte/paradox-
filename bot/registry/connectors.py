import sqlite3 as sq
import mysql.connector

from .Connector import Connector


class mysqlConnector(Connector):
    db_type = 'mysql'
    replace_char = '%s'
    cursor_args = {"dictionary": True}

    def __init__(self, **dbopts):
        super().__init__(**dbopts)

        self.conn = mysql.connector.connect(**dbopts)


class sqliteConnector(Connector):
    db_type = 'sqlite'
    replace_char = '?'
    timeout = 20

    def __init__(self, **dbopts):
        super().__init__(**dbopts)

        data_file = dbopts.get("db_file")
        self.conn = sq.connect(data_file, timeout=dbopts.get("timeout", self.timeout))
        self.conn.row_factory = sq.Row
