from enum import Enum


class ColumnType(Enum):
    """
    Describes several common database column data types,
    and describes the types for python, mysql and sqlite.
    """
    INT = (int, 'INT', 'INTEGER')
    SNOWFLAKE = (int, 'BIGINT', 'INTEGER')
    SHORTSTRING = (str, 'VARCHAR(64)', 'TEXT')
    MSGSTRING = (str, 'VARCHAR(2048)', 'TEXT')
    TEXT = (str, 'TEXT', 'TEXT')
    BOOL = (bool, 'BOOLEAN', 'BOOL')

    @property
    def pytype(self):
        return self.value[0]

    @property
    def in_mysql(self):
        return self.value[1]

    @property
    def in_sqlite(self):
        return self.value[2]


class Column:
    """
    Simple class to describe a column in a simple table design.

    Parameters
    ----------
    column_name: str
        Name of the column being described.
    column_type: ColumnType
        Type of the column.
    primary: Bool
        Whether this column is a primary key.
    required: Bool
        Whether this column is required not to be NULL.
    """
    def __init__(self, column_name, column_type, primary=False, required=False, default=None):
        self.name = column_name
        self.col_type = column_type
        self.primary = primary
        self.required = required
        self.default = default

    @property
    def for_mysql(self):
        return "{} {}{}{}".format(
            self.name,
            self.col_type.in_mysql,
            " NOT NULL" if self.required else "",
            " DEFAULT {}".format(self.default) if self.default is not None else ""
        )

    @property
    def for_sqlite(self):
        return "{} {}{}{}".format(
            self.name,
            self.col_type.in_sqlite,
            " NOT NULL" if self.required else "",
            " DEFAULT {}".format(self.default) if self.default is not None else ""
        )


def schema_generator(table_name, *columns):
    """
    Helper to generate a mysql and sqlite schema for a simple table design.

    Parameters
    ----------
    table_name: str
        Name of the table to generate the schema for.
    columns: List[Column]

    Returns: Tuple[str, str, Tuple[Tuple[str, type]]]
        Represents `(mysql_schema, sqlite_schema, column_data)`
        where `column_data` is that accepted by `tableManipulator`.
    """
    table_formatstr = "CREATE TABLE {table}(\n\t{col_strs}{primary_str}\n);"

    primary_keys = ','.join(column.name for column in columns if column.primary)
    primary_key_str = ",\n\tPRIMARY KEY ({})".format(primary_keys) if primary_keys else ""

    # Generate mysql schema
    mysql_col_strs = ',\n\t'.join(column.for_mysql for column in columns)
    mysql_schema = table_formatstr.format(
        table=table_name,
        col_strs=mysql_col_strs,
        primary_str=primary_key_str
    )

    # Generate sqlite schema
    sqlite_col_strs = ',\n\t'.join(column.for_sqlite for column in columns)
    sqlite_schema = table_formatstr.format(
        table=table_name,
        col_strs=sqlite_col_strs,
        primary_str=primary_key_str
    )

    # Generate column data
    column_tuple = tuple(((c.name, c.col_type.pytype) for c in columns))

    return (mysql_schema, sqlite_schema, column_tuple)
