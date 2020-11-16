from registry import schema_generator, Column, ColumnType, tableInterface

from ..module import latex_module as module


# Define data schema
preamble_schemas = schema_generator(
    "guild_latex_preambles",
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('preamble', ColumnType.TEXT, primary=False, required=True),
)

config_schemas = schema_generator(
    "guild_latex_config",
    Column('app', ColumnType.SHORTSTRING, primary=True, required=True),
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('autotex', ColumnType.BOOL, primary=False, required=False),
    Column('autotex_level', ColumnType.INT, primary=False, required=False),
    Column('require_codeblocks', ColumnType.BOOL, primary=False, required=False),
)

channel_schemas = schema_generator(
    "guild_latex_channels",
    Column('app', ColumnType.SHORTSTRING, primary=True, required=True),
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('channelid', ColumnType.SNOWFLAKE, primary=True, required=True),
)


# Attach data interfaces
@module.data_init_task
def attach_latexguild_data(client):
    mysql_schema, sqlite_schema, columns = preamble_schemas
    interface = tableInterface(
        client.data,
        "guild_latex_preambles",
        app=client.app,
        column_data=columns,
        shared=True,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "guild_latex_preambles")

    mysql_schema, sqlite_schema, columns = config_schemas
    interface = tableInterface(
        client.data,
        "guild_latex_config",
        app=client.app,
        column_data=columns,
        shared=False,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "guild_latex_config")

    mysql_schema, sqlite_schema, columns = channel_schemas
    interface = tableInterface(
        client.data,
        "guild_latex_channels",
        app=client.app,
        column_data=columns,
        shared=False,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "guild_latex_channels")
