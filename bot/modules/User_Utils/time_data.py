from registry import schema_generator, Column, ColumnType, tableInterface

from .module import utils_module as module


schemas = schema_generator(
    "user_time_settings",
    Column('userid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('timezone', ColumnType.SHORTSTRING),
    Column('brief_display', ColumnType.BOOL, default=False),
)


# Attach data interfaces
@module.data_init_task
def attach_time_settings_data(client):
    mysql_schema, sqlite_schema, columns = schemas
    interface = tableInterface(
        client.data,
        "user_time_settings",
        app=client.app,
        column_data=columns,
        shared=True,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "user_time_settings")
