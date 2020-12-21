import discord
from datetime import datetime

from settings import GuildSetting, Channel, ColumnData
from registry import tableInterface, schema_generator, Column, ColumnType

from wards import guild_manager

from .module import guild_logging_module as module


async def log_member_update(bot, before, after):
    userlog = await bot.data.servers.get(before.server.id, "userlog_ch")
    if not userlog:
        return
    userlog = before.server.get_channel(userlog)
    if not userlog:
        return

    log_ignore = await bot.data.servers.get(before.server.id, "userlog_ignore")
    if log_ignore and (before.id in log_ignore):
        return

    events = await bot.data.servers.get(before.server.id, "userlog_events")

    desc_lines = []
    image_url = None
    if (events is None or "username" in events) and before.name != after.name:
        desc_lines.append("{}#{} ({}) changed their username.".format(after.name, after.discriminator, after.mention))
        desc_lines.append("`Before:` {}".format(before.name))
        desc_lines.append("`After:` {}".format(after.name))

    if (events is None or "nickname" in events) and before.nick != after.nick:
        desc_lines.append("{}#{} ({}) changed their nickname.".format(after.name, after.discriminator, after.mention))
        desc_lines.append("`Before:` {}".format(before.nick))
        desc_lines.append("`After:` {}".format(after.nick))

    if (events is None or "avatar" in events) and before.avatar_url != after.avatar_url:
        desc_lines.append("{}#{} ({}) changed their avatar.".format(after.name, after.discriminator, after.mention))
        old_av = "[Old Avatar]({})".format(before.avatar_url) if before.avatar_url else "None"
        new_av = "[New Avatar]({})".format(after.avatar_url) if after.avatar_url else "None"
        desc_lines.append("`Before:` {}".format(old_av))
        desc_lines.append("`After:` {}".format(new_av))
        image_url = after.avatar_url if after.avatar_url else None

    if (events is None or "roles" in events) and before.roles != after.roles:
        before_roles = [role.name for role in before.roles]
        after_roles = [role.name for role in after.roles]
        added_roles = [role for role in after_roles if role not in before_roles]
        removed_roles = [role for role in before_roles if role not in after_roles]
        desc_lines.append("The roles of {}#{} ({}) were modified.".format(after.name, after.discriminator, after.mention))
        if added_roles:
            desc_lines.append("Added roles `{}`".format("`, `".join(added_roles)))
        if removed_roles:
            desc_lines.append("Removed roles `{}`".format("`, `".join(removed_roles)))

    if not desc_lines:
        return

    description = "\n".join(desc_lines)
    colour = (after.colour if after.colour.value else discord.Colour.light_grey())

    embed = discord.Embed(color=colour, description=description, timestamp=datetime.now())
    if image_url:
        embed.set_thumbnail(url=image_url)
    await bot.send_message(userlog, embed=embed)

channel_schema_info = schema_generator(
    "guild_userupdate_channel",
    Column('app', ColumnType.SHORTSTRING, primary=True, required=True),
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('channelid', ColumnType.SNOWFLAKE),  # Channel to log the userupdates to
)

event_schema_info = schema_generator(
    "guild_userupdate_events",
    Column('app', ColumnType.SHORTSTRING, primary=True, required=True),
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('event', ColumnType.INT, primary=True, required=True),  # The event types to log
)

ignores_schema_info = schema_generator(
    "guild_userupdate_ignores",
    Column('app', ColumnType.SHORTSTRING, primary=True, required=True),
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('userid', ColumnType.SNOWFLAKE, primary=True, required=True),
)


# Attach data interfaces
@module.data_init_task
def attach_userlog_data(client):
    mysql_schema, sqlite_schema, columns = channel_schema_info
    prefix_interface = tableInterface(
        client.data,
        "guild_userupdate_channel",
        app=client.app,
        column_data=columns,
        shared=False,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema
    )
    client.data.attach_interface(prefix_interface, "guild_userupdate_channel")

    mysql_schema, sqlite_schema, columns = event_schema_info
    prefix_interface = tableInterface(
        client.data,
        "guild_userupdate_events",
        app=client.app,
        column_data=columns,
        shared=False,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema
    )
    client.data.attach_interface(prefix_interface, "guild_userupdate_events")

    mysql_schema, sqlite_schema, columns = ignores_schema_info
    prefix_interface = tableInterface(
        client.data,
        "guild_userupdate_events",
        app=client.app,
        column_data=columns,
        shared=False,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema
    )
    client.data.attach_interface(prefix_interface, "guild_userupdate_ignores")
