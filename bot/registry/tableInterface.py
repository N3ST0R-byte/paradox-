from .Connector import Connector
from .Interface import Interface


# TODO: App-aware interface with an app column
class tableInterface(Interface):
    """
    Data interface containing standard methods to access a single table.
    Acts as a  wrapper around the connector for a single table,
    with some optional type checking.
    """

    _mysql_schema = None
    _sqlite_schema = None

    def __init__(self, conn: Connector, table_name, app, column_data, mysql_schema=None, sqlite_schema=None):
        self.conn = conn
        self.table = table_name
        self.app = app

        self.mysql_schema = mysql_schema or self._mysql_schema
        self.sqlite_schema = sqlite_schema or self._sqlite_schema

        self.columns = {p[0]: p[1] for p in column_data}

    @property
    def schema(self):
        if self.conn.db_type == "sqlite":
            return self.sqlite_schema
        elif self.conn.db_type == "mysql":
            return self.mysql_schema

    def check_keys(self, params):
        for param, value in params.items():
            if param not in self.columns:
                raise ValueError("Invalid column '{}' passed to table interface '{}'".format(param, self.table))
            elif self.columns[param] is not None and not isinstance(value, self.columns[param]):
                raise TypeError("Incorrect type '{}' passed for key '{}' in table interface '{}'".format(
                    type(value), param, self.table
                ))

    def select_where(self, select_columns=None, **conditions):
        self.check_keys(conditions)
        return self.conn.select_where(self.table, select_columns=select_columns, **conditions)

    def update_where(self, valuedict, **conditions):
        self.check_keys(conditions)
        return self.conn.update_where(self.table, valuedict, **conditions)

    def delete_where(self, **conditions):
        self.check_keys(conditions)
        return self.conn.delete_where(self.table, **conditions)

    def insert(self, allow_replace=False, **values):
        self.check_keys(values)
        return self.conn.insert(self.table, allow_replace=allow_replace, **values)

    def insert_many(self, *value_tuples, insert_keys=None):
        if insert_keys:
            for v_tuple in value_tuples:
                values = {key: value for key, value in zip(insert_keys, v_tuple)}
                self.check_keys(values)

        return self.conn.insert_many(self.table, *value_tuples, insert_keys=insert_keys)
