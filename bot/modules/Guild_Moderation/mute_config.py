from settings import ColumnData, Role, GuildSetting
from registry import tableInterface, Column, ColumnType, schema_generator

from wards import guild_admin

from .module import guild_moderation_module as module


# Define the guild setting
@module.guild_setting
class muterole(ColumnData, Role, GuildSetting):
    attr_name = "muterole"
    category = "Moderation"

    read_check = None
    write_check = guild_admin

    name = "muterole"
    desc = "Permission-limited role given to muted or jail users."

    long_desc = (
        "Role to give and remove with the `mute` and `unmute` commands.\n"
        "In order to use the role, I must have the `manage roles` permission, "
        "in a role above the muterole."
    )

    _table_interface_name = "guild_muteroles"
    _data_column = "roleid"


# Define data schema
mysql_schema, sqlite_schema, columns = schema_generator(
    "guild_muteroles",
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('roleid', ColumnType.SNOWFLAKE, primary=False, required=True),
)


# Attach data interface
@module.data_init_task
def attach_muterole_data(client):
    muterole_interface = tableInterface(
        client.data,
        "guild_muteroles",
        app=client.app,
        column_data=columns,
        shared=True,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(muterole_interface, "guild_muteroles")
