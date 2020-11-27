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
    TIMESTAMP = (int, 'TIMESTAMP', 'TIMESTAMP')

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
    default: Any
        The default value for the column.
    mysql_update_timestamp: Bool
        Whether to add `ON UPDATE CURRENT_TIMESTAMP` to the column.
        Only applies to mysql.
    """
    def __init__(self, column_name, column_type,
                 primary=False, required=False, default=None,
                 mysql_update_timestamp=False):
        self.name = column_name
        self.col_type = column_type
        self.primary = primary
        self.required = required
        self.default = default
        self.update_timestamp = mysql_update_timestamp

    @property
    def for_mysql(self):
        return "{} {}{}{}{}".format(
            self.name,
            self.col_type.in_mysql,
            " NOT NULL" if self.required else "",
            " DEFAULT {}".format(self.default) if self.default is not None else "",
            " ON UPDATE CURRENT_TIMESTAMP" if self.update_timestamp else ""
        )

    @property
    def for_sqlite(self):
        return "{} {}{}{}".format(
            self.name,
            self.col_type.in_sqlite,
            " NOT NULL" if self.required else "",
            " DEFAULT {}".format(self.default) if self.default is not None else ""
        )


def timestamp_column(name, required=False):
    """
    Quick helper to generate an automatic timestamp column.
    """
    return Column(
        name,
        ColumnType.TIMESTAMP,
        required=required,
        default="CURRENT_TIMESTAMP",
        mysql_update_timestamp=True
    )


def schema_generator(table_name, *columns, add_timestamp=True, add_app=False):
    """
    Helper to generate a mysql and sqlite schema for a simple table design.

    Parameters
    ----------
    table_name: str
        Name of the table to generate the schema for.
    columns: List[Column]
        List of Columns to add to the schema.
    add_timestamp: bool
        Whether to automatically add a `_timestamp` column with the insert timestamp.
        On mysql this column also updates on update.
    add_app: bool
        Whether to automatically add an `app` column for the current app.

    Returns: Tuple[str, str, Tuple[Tuple[str, type]]]
        Represents `(mysql_schema, sqlite_schema, column_data)`
        where `column_data` is that accepted by `tableManipulator`.
    """
    if add_timestamp:
        columns = (*columns, timestamp_column('_timestamp'))
    if add_app:
        columns = (*columns, Column('app', ColumnType.SHORTSTRING, primary=True, required=True))

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
