from registry import schema_generator, Column, ColumnType, tableInterface

from .module import meta_module as module


# Define data schema
schemas = schema_generator(
    "user_prefixes",
    Column('app', ColumnType.SHORTSTRING, primary=True, required=True),
    Column('userid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('prefix', ColumnType.SHORTSTRING, required=True)
)


# Attach data interfaces
@module.data_init_task
def attach_prefix_data(client):
    mysql_schema, sqlite_schema, columns = schemas
    interface = tableInterface(
        client.data,
        "user_prefixes",
        app=client.app,
        column_data=columns,
        shared=False,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "user_prefixes")


# Cache user prefixes
@module.init_task
def load_userprefix_cache(client):
    user_prefixes = {
        row['userid']: row['prefix']
        for row in client.data.user_prefixes.select_where()
    }
    client.objects["user_prefix_cache"] = user_prefixes

    client.log("Read {} users with custom prefixes.".format(len(user_prefixes)),
               context="LOAD_USER_PREFIXES")
