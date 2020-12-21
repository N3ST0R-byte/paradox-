import logging
import asyncio
from datetime import datetime
import discord
from discord import Status

from settings import GuildSetting, Channel, ColumnData
from registry import tableInterface, schema_generator, Column, ColumnType

from utils.lib import strfdelta, prop_tabulate, format_activity, join_list
from wards import guild_manager

from .module import guild_logging_module as module


# Map providing human readable names for each status
statusnames = {
    Status.offline: "Offline",
    Status.dnd: "Do Not Disturb",
    Status.online: "Online",
    Status.idle: "Away",
}

# Statuses which are considered as active
activestatus = [Status.online, Status.idle, Status.dnd]


# Member join log event handler
async def join_logger(client, member):
    # Get the joinlog, return if it doesn't exist
    joinlog = client.guild_config.join_log.get(client, member.guild.id).value
    if not joinlog:
        return

    # Re-fetch the member to get better presence information
    await asyncio.sleep(1)
    member = member.guild.get_member(member.id)
    if member is None:
        return

    # Extract the required user information
    colour = member.colour if member.colour.value else discord.Colour.green()
    name = "{} {} ({})".format(
        member,
        client.conf.emojis.getemoji("bot") if member.bot else "",
        member.mention
    )
    activity = format_activity(member)
    presence = "{} {}".format(client.conf.emojis.getemoji(member.status.name), statusnames[member.status])
    created_ago = "({} ago)".format(strfdelta(datetime.utcnow() - member.created_at, minutes=False))
    created = member.created_at.strftime("%I:%M %p, %d/%m/%Y")

    devicestatus = {
        "desktop": member.desktop_status in activestatus,
        "mobile": member.mobile_status in activestatus,
        "web": member.web_status in activestatus,
    }
    if any(devicestatus.values()):
        # String if the member is "online" on one or more devices.
        device = "Active on **{}**".format(join_list(string=[k for k, v in devicestatus.items() if v], nfs=True))
    else:
        # String if the user isn't "online" on any device.
        device = "Not active on any device"

    member_count = "{} Users, {} Bots | {} total".format(
        len([m for m in member.guild.members if not m.bot]),
        len([m for m in member.guild.members if m.bot]),
        member.guild.member_count
    )

    # Build the log embed
    prop_list = ["User", "Presence", "Activity", "Device", "Created at", "", "Member Count"]
    value_list = [name, presence, activity, device, created, created_ago, member_count]
    desc = prop_tabulate(prop_list, value_list)

    embed = discord.Embed(
        color=colour,
        title="{user} ({user.id})".format(user=member),
        description=desc,
        timestamp=datetime.now()
    )
    embed.set_author(
        name="New {usertype} joined!".format(usertype='bot' if member.bot else 'user'),
        url=member.avatar_url
    )
    embed.set_thumbnail(url=member.avatar_url)

    try:
        await joinlog.send(embed=embed)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass
    except Exception as e:
        client.log("Failed to post joinlog for member '{}' (uid:{}) in guild '{} (gid:{})."
                   " Exception: {}".format(member,
                                           member.id,
                                           member.guild.name,
                                           member.guild.id,
                                           e.__repr__()),
                   context="POST_JOINLOG",
                   level=logging.WARNING)


# member departure log event handler
async def departure_logger(client, member):
    # Get the departure log, return if it doesn't exist
    departure_log = client.guild_config.departure_log.get(client, member.guild.id).value
    if not departure_log:
        return

    # Extract member information
    name = "{} ({})".format(member.display_name, member.mention)
    colour = discord.Colour.red()
    avatar = member.avatar_url

    joined_ago = "({} ago)".format(strfdelta(datetime.utcnow() - member.joined_at, minutes=False))
    joined = member.joined_at.strftime("%I:%M %p, %d/%m/%Y")

    roles = reversed([r.mention for r in member.roles if not r.is_default()])
    rolestr = ", ".join(roles) if len(roles) > 0 else "None"

    member_count = "{} Users, {} Bots | {} total".format(
        len([m for m in member.guild.members if not m.bot]),
        len([m for m in member.guild.members if m.bot]),
        member.guild.member_count
    )

    prop_list = ["Member", "Joined at", "", "Roles", "Member count"]
    value_list = [name, joined, joined_ago, rolestr, member_count]
    desc = prop_tabulate(prop_list, value_list)

    embed = discord.Embed(
        color=colour,
        title="{user} ({user.id})".format(user=member),
        description=desc,
        timestamp=datetime.now()
    )
    embed.set_author(
        name="{usertype} left!".format(usertype='Bot' if member.bot else 'User'),
        url=avatar
    )
    embed.set_thumbnail(url=avatar)

    try:
        await departure_log.send(embed=embed)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass
    except Exception as e:
        client.log("Failed to post departure log for member '{}' (uid:{}) in guild '{} (gid:{})."
                   " Exception: {}".format(member,
                                           member.id,
                                           member.guild.name,
                                           member.guild.id,
                                           e.__repr__()),
                   context="POST_DEPARTURELOG",
                   level=logging.WARNING)


# Attach event handlers
@module.init_task
def attach_traffic_handlers(client):
    client.add_after_event('member_join', join_logger)
    client.add_after_event('member_remove', departure_logger)


# Define configuration settings
@module.guild_setting
class guild_joinlog(ColumnData, Channel, GuildSetting):
    attr_name = "join_log"
    category = "Logging"
    read_check = None
    write_check = guild_manager

    name = "join_log"
    desc = "Channel where new member information is posted."

    long_desc = ("Channel where information about new members is posted.")

    _table_interface_name = "guild_join_logging"
    _data_column = "channelid"
    _delete_on_none = True


@module.guild_setting
class guild_departurelog(ColumnData, Channel, GuildSetting):
    attr_name = "departure_log"
    category = "Logging"
    read_check = None
    write_check = guild_manager

    name = "departure_log"
    desc = "Channel where information about departing members is posted."

    long_desc = "Channel where information about departing members is posted."

    _table_interface_name = "guild_departure_logging"
    _data_column = "channelid"
    _delete_on_none = True


# Define data schemas
member_traffic_schema_info = schema_generator(
    "member_traffic",
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('userid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('first_joined', ColumnType.INT),  # Timestamp of first join seen or inferred
    Column('last_joined', ColumnType.INT),  # Timestamp of join at last departure
    Column('last_departure', ColumnType.INT),  # Timestamp of last departure
    Column('departure_name', ColumnType.SHORTSTRING),  # Name of user at last departure
    Column('departure_nickname', ColumnType.SHORTSTRING),  # Nickname of user at last departure
)

join_log_schema_info = schema_generator(
    "guild_join_logging",
    Column('app', ColumnType.SHORTSTRING, primary=True, required=True),
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('channelid', ColumnType.INT, required=True),
)

departure_log_schema_info = schema_generator(
    "guild_departure_logging",
    Column('app', ColumnType.SHORTSTRING, primary=True, required=True),
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('channelid', ColumnType.INT, required=True),
)


# Attach data interfaces
@module.data_init_task
def attach_traffic_data(client):
    mysql_schema, sqlite_schema, columns = member_traffic_schema_info
    prefix_interface = tableInterface(
        client.data,
        "member_traffic",
        app=client.app,
        column_data=columns,
        shared=True,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema
    )
    client.data.attach_interface(prefix_interface, "member_traffic")

    mysql_schema, sqlite_schema, columns = join_log_schema_info
    prefix_interface = tableInterface(
        client.data,
        "guild_join_logging",
        app=client.app,
        column_data=columns,
        shared=False,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema
    )
    client.data.attach_interface(prefix_interface, "guild_join_logging")

    mysql_schema, sqlite_schema, columns = departure_log_schema_info
    prefix_interface = tableInterface(
        client.data,
        "guild_departure_logging",
        app=client.app,
        column_data=columns,
        shared=False,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema
    )
    client.data.attach_interface(prefix_interface, "guild_departure_logging")
