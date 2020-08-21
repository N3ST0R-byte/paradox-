import discord
from cmdClient import Context
from wards import in_guild
from datetime import datetime
from utils.lib import emb_add_fields, paginate_list, strfdelta, prop_tabulate, format_activity, join_list
from constants import region_map, ParaCC

from .module import info_module as module

# Provides serverinfo, userinfo, roleinfo, whohas, avatar
"""
Provides a number of information providing commands

Commands provided:
    userinfo:
        Provides info on the provided user
    avatar:
        Displays the avatar for the provided user
    role:
        Displays info on the provided role, or displays a list of roles
    rolemembers:
        Displays the members of a role
    serverinfo:
        Displays info on the current server
    channelinfo:
        Displays information about a specified channel
"""


@module.cmd(name="roleinfo",
            desc="Displays information about a role",
            aliases=["role", "rinfo", "ri"])
@in_guild()
async def cmd_role(ctx: Context):
    """
    Usage``:
        {prefix}roleinfo [<role-name> | <role-mention> | <role-id>]
    Description:
        Provides information about the given role.
    """
    guild_roles = sorted(ctx.guild.roles, key=lambda role: role.position)

    if ctx.arg_str.strip() == "":
        await ctx.pager(paginate_list([role.name for role in reversed(guild_roles)], title="Guild roles"))
        return
    role = await ctx.find_role(ctx.arg_str, create=False, interactive=True)
    if role is None:
        return

    title = "{role.name} ({role.id})".format(role=role)

    colour = role.colour if role.colour.value else discord.Colour.light_grey()
    num_users = len([user for user in ctx.guild.members if (role in user.roles)])
    created_ago = "({} ago)".format(strfdelta(datetime.utcnow() - role.created_at, minutes=False))
    created = role.created_at.strftime("%I:%M %p, %d/%m/%Y")
    hoisted = "Yes" if role.hoist else "No"
    mentionable = "Yes" if role.mentionable else "No"

    prop_list = ["Colour", "Hoisted", "Mentionable", "Number of members", "Created at", ""]
    value_list = [str(role.colour), hoisted, mentionable, num_users, created, created_ago]
    desc = prop_tabulate(prop_list, value_list)

    pos = role.position
    position = "```markdown\n"
    for i in reversed(range(-3, 4)):
        line_pos = pos + i
        if line_pos < 0:
            break
        if line_pos >= len(guild_roles):
            continue
        position += "{0:<4}{1}{2:<20}\n".format(str(line_pos) + ".", " " * 4 + ("> " if str(guild_roles[line_pos]) == str(role) else "  "), str(guild_roles[line_pos]))
    position += "```"
    if not ctx.guild.default_role == ctx.author.top_role:
        if role > ctx.author.top_role:
            diff_str = "(Higher than your highest role)"
        elif role < ctx.author.top_role:
            diff_str = "(Lower than your highest role)"
        elif role == ctx.author.top_role:
            diff_str = "(This is your highest role!)"
        position += diff_str

    embed = discord.Embed(title=title, colour=colour, description=desc)
    emb_fields = [("Position in the hierarchy", position, 0)]
    await emb_add_fields(embed, emb_fields)
    await ctx.reply(embed=embed)


@module.cmd(name="rolemembers",
            desc="Lists members with a particular role.",
            aliases=["rolemems", "whohas"])
@in_guild()
async def cmd_rolemembers(ctx: Context):
    """
    Usage``:
        {prefix}rolemembers [<role-name> | <role-mention> | <role-id>]
    Description:
    Lists the users with this role.
     """

    if ctx.arg_str.strip() == "":
        return await ctx.error_reply("Please provide a role to list the members of.")

    role = await ctx.find_role(ctx.arg_str, create=False, interactive=True)
    if role is None:
        return

    members = [str(mem) for mem in ctx.guild.members if role in mem.roles]
    if len(members) == 0:
        await ctx.reply("No members have this role.")
        return
    await ctx.pager(paginate_list(members, title="Members in {}".format(role.name)))


@module.cmd("userinfo",
            desc="Shows various information about a user.",
            aliases=["uinfo", "ui", "user"])
@in_guild()
async def cmd_userinfo(ctx: Context):
    """
    Usage``:
        {prefix}userinfo [user]
    Description:
        Sends information on the provided user, or yourself.
    """

    user = ctx.author
    if ctx.arg_str != "":
        user = await ctx.find_member(ctx.arg_str, interactive=True)
        if not user:
            await ctx.reply("No matching users found!")
            return
    # Manually get a new user in case the old one was out of date
    new_user = await ctx.client.fetch_user(user.id)

    bot_emoji = ctx.client.conf.emojis.getemoji("bot")
    presencedict = {"offline": ("Offline", ctx.client.conf.emojis.getemoji("offline")),
                    "dnd": ("Do Not Disturb", ctx.client.conf.emojis.getemoji("dnd")),
                    "online": ("Online", ctx.client.conf.emojis.getemoji("online")),
                    "idle": ("Away", ctx.client.conf.emojis.getemoji("idle"))}
    colour = (user.colour if user.colour.value else discord.Colour.light_grey())

    name = "{} {}".format(user, bot_emoji if user.bot else "")

    # Acceptable statuses to be considered as online. 
    statuses = [discord.Status.online, discord.Status.idle, discord.Status.dnd]

    devices = {
        "desktop": { 
            "value": False,
        },
        "mobile": {
            "value": False,
        },
        "web": {
            "value": False
        }
    }

    # Set the respective value to True in the devices dict if the user is "online" on that device.
    if user.desktop_status in statuses:
        devices["desktop"]["value"] = True
    if user.mobile_status in statuses:
        devices["mobile"]["value"] = True
    if user.web_status in statuses:
        devices["web"]["value"] = True

    # String if the user is "online" on one or more devices.
    device = "Active on {}".format(join_list(string=[i for i in devices if devices[i]["value"] is True]))
    # String if the user isn't "online" on any device.
    if all(value["value"] is False for value in devices.values()):
        device = "Offline on every device."

    activity = format_activity(user)
    presence = "{1} {0}".format(*presencedict[str(user.status)])
    numshared = len(list(filter(lambda m: m.id == user.id, ctx.client.get_all_members())))
    shared = "{} guild{}.".format(numshared, "s" if numshared > 1 else "")
    joined_ago = "({} ago)".format(strfdelta(datetime.utcnow() - user.joined_at, minutes=False))
    joined = user.joined_at.strftime("%I:%M %p, %d/%m/%Y")
    created_ago = "({} ago)".format(strfdelta(datetime.utcnow() - user.created_at, minutes=False))
    created = user.created_at.strftime("%I:%M %p, %d/%m/%Y")
    usernames = ctx.client.data.users.get(user.id, "name_history")
    name_list = "{}{}".format("..., " if len(usernames) > 10 else "",
                              ", ".join(usernames[-10:])) if usernames else "No recent past usernames."
    nicknames = ctx.client.data.members.get(ctx.guild.id, user.id, "nickname_history")
    nickname_list = "{}{}".format("..., " if len(nicknames) > 10 else "",
                                  ", ".join(nicknames[-10:])) if nicknames else "No recent past nicknames."
    prop_list = ["Full name", "Nickname", "Presence", "Activity", "Device", "Names", "Nicknames", "Seen in", "Joined at", "", "Created at", ""]
    value_list = [name, user.display_name, presence, activity, device, name_list, nickname_list, shared, joined, joined_ago, created, created_ago]
    desc = prop_tabulate(prop_list, value_list)

    roles = [r.name for r in user.roles if r.name != "@everyone"]
    roles = ('`' + '`, `'.join(roles) + '`') if roles else "None"

    joined = sorted(ctx.guild.members, key=lambda mem: mem.joined_at)
    pos = joined.index(user)
    positions = []
    for i in range(-3, 4):
        line_pos = pos + i
        if line_pos < 0:
            continue
        if line_pos >= len(joined):
            break
        positions.append("{0:<4}{1}{2:<20}".format(str(line_pos + 1) + ".", " " * 4 + ("> " if joined[line_pos] == user else "  "), str(joined[line_pos])))
    join_seq = "```markdown\n{}\n```".format("\n".join(positions))

    embed = discord.Embed(color=colour, description=desc)
    embed.set_author(name="{user} ({user.id})".format(user=new_user),
                     icon_url=new_user.avatar_url)
    embed.set_thumbnail(url=new_user.avatar_url)

    emb_fields = [("Roles", roles, 0), ("Join order", join_seq, 0)]
    await emb_add_fields(embed, emb_fields)
    await ctx.reply(embed=embed)


@module.cmd("serverinfo",
            desc="Shows information about the guild.",
            aliases=["sinfo", "si", "guildinfo", "gi"],
            flags=["icon"])
@in_guild()
async def cmd_serverinfo(ctx: Context, flags):
    """
    Usage``:
        {prefix}serverinfo [--icon]
    Description:
        Shows information about the server you are in.
        With --icon, just displays the server icon.
    """
    if flags["icon"]:
        embed = discord.Embed(color=discord.Colour.light_grey())
        embed.set_image(url=ctx.guild.icon_url)
        return await ctx.reply(embed=embed)

    region = str(ctx.guild.region) if not str(ctx.guild.region) in region_map else region_map[str(ctx.guild.region)]

    ver = {
        "none": "None | Unrestricted",
        "low": "Low | Must have a verified email",
        "medium": "Medium | Must be registered for more than 5 minutes",
        "high": "High | Must be a member for more than 10 minutes",
        "extreme": "Highest | Must have a verified phone number"
    }

    mfa = {
        0: "Disabled",
        1: "Enabled"
    }

    text = len([c for c in ctx.guild.channels if c.type == discord.ChannelType.text])
    voice = len([c for c in ctx.guild.channels if c.type == discord.ChannelType.voice])
    category = len([c for c in ctx.guild.categories])
    total = text + voice + category

    online = 0
    idle = 0
    offline = 0
    dnd = 0
    for m in ctx.guild.members:
        if m.status == discord.Status.online:
            online = online + 1
        elif m.status == discord.Status.idle:
            idle = idle + 1
        elif m.status == discord.Status.offline:
            offline = offline + 1
        elif m.status == discord.Status.dnd:
            dnd = dnd + 1

    safestatus = [discord.Status.online, discord.Status.idle, discord.Status.dnd]
    desktop = 0
    mobile = 0
    web = 0 
    for m in ctx.guild.members:
        if m.desktop_status in safestatus:
            desktop = desktop + 1
        elif m.mobile_status in safestatus:
            mobile = mobile + 1
        elif m.web_status in safestatus:
            web = web + 1
    devicestatus = "🖥️ - **{}**\n📱 - **{}**\n🌎 - **{}**".format(desktop, mobile, web)
    Online = ctx.client.conf.emojis.getemoji("online")
    Offline = ctx.client.conf.emojis.getemoji("offline")
    Idle = ctx.client.conf.emojis.getemoji("idle")
    Dnd = ctx.client.conf.emojis.getemoji("dnd")

    server_owner = ctx.guild.owner
    owner = "{} ({})".format(server_owner, server_owner.id)
    members = "{} humans, {} bots | {} total".format(str(len([m for m in ctx.guild.members if not m.bot])),
                                                     str(len([m for m in ctx.guild.members if m.bot])),
                                                     ctx.guild.member_count)
    created = ctx.guild.created_at.strftime("%I:%M %p, %d/%m/%Y")
    created_ago = "({} ago)".format(strfdelta(datetime.utcnow() - ctx.guild.created_at, minutes=False))
    channels = "{} text, {} voice, {} categories | {} total".format(text, voice, category, total)
    status = "{} - **{}**\n{} - **{}**\n{} - **{}**\n{} - **{}**".format(Online, online, Idle, idle, Dnd, dnd, Offline, offline)
    icon = "[Icon Link]({})".format(ctx.guild.icon_url)
    is_large = "More than 250 members" if ctx.guild.large else "Less than 250 members"
    boosts = "Level {} | {} boosts total".format(ctx.guild.premium_tier, ctx.guild.premium_subscription_count)

    prop_list = ["Owner", "Region", "Icon", "Large server?", "Verification", "2FA", "Roles", "Members", "Channels", "Server Boosts", "Created at", ""]
    value_list = [owner,
                  region,
                  icon,
                  is_large,
                  ver[str(ctx.guild.verification_level)],
                  mfa[ctx.guild.mfa_level],
                  len(ctx.guild.roles),
                  members, channels, boosts, created, created_ago]
    desc = prop_tabulate(prop_list, value_list)

    embed = discord.Embed(color=server_owner.colour if server_owner.colour.value else discord.Colour.teal(), description=desc)
    embed.set_author(name="{} ({})".format(ctx.guild, ctx.guild.id))
    embed.set_thumbnail(url=ctx.guild.icon_url)

    emb_fields = [("Member Status", status, 0), ("Member Status by Device", devicestatus, 0)]

    await emb_add_fields(embed, emb_fields)
    await ctx.reply(embed=embed)


@module.cmd("channelinfo",
            desc="Displays information about a channel.",
            aliases=["ci"])
@in_guild()
async def cmd_channelinfo(ctx: Context):
    """
    Usage``:
        {prefix}channelinfo [<channel-name> | <channel-mention> | <channel-id]
    Description:
        Gives information on a text channel, voice channel, or category.
    """
    tv = {
        "text": "Text channel",
        "voice": "Voice channel",
        "category": "Category",
        "news": "Announcement channel",
        "store": "Store channel"
    }

    text_types = [discord.ChannelType.text, discord.ChannelType.news]

    # Disallow selecting channels that the user cannot see. Channels the bot can see still work.
    valid_channels = [ch for ch in ctx.guild.channels if ch.permissions_for(ctx.author).read_messages]
    if not ctx.arg_str:
        ch = ctx.ch
    else:
        ch = await ctx.find_channel(ctx.arg_str, interactive=True, collection=valid_channels)
        if not ch:
            return
    # Generic embed info, valid for every channel type. 
    name = f"{ch.name} [{ch.mention}]" if ch.type in text_types else f"{ch.name}"
    createdat = ch.created_at.strftime("%d/%m/%Y")
    created_ago = f"({strfdelta(datetime.utcnow() - ch.created_at, minutes=True)} ago)"
    atgo = f"{createdat} {created_ago}"

    if ch.category:
        category = f"{ch.category} ({ch.category_id})"
    else:
        category = "Uncategorised" 

    # Embed info specific to text channels.
    if ch.type in text_types:
        topic = ch.topic if ch.topic else "No topic."
        if ch.nsfw:
            nsfw = "Yes"
        else: 
            nsfw = "No"
        prop_list = ["Name", "Type", "ID", "NSFW", "Category", "Created at", "Topic"]
        value_list = [name, tv[str(ch.type)], ch.id, nsfw, category, atgo, topic]

    # Embed info specific to voice channels.
    elif ch.type == discord.ChannelType.voice:
        if ch.user_limit == 0:
            userlimit = "Unlimited"
        else:
            userlimit = ch.user_limit

        prop_list = ["Name", "Type", "ID", "Category", "Created at", "User limit"]
        value_list = [name, tv[str(ch.type)], ch.id, category, atgo, userlimit]

    # If any other type is present, provide generic information only.
    else:
        prop_list = ["Name", "Type", "ID", "Created at"]
        value_list = [name, tv[str(ch.type)], ch.id, atgo]

    desc = prop_tabulate(prop_list, value_list)
    embed = discord.Embed(color=ParaCC["blue"], description=desc)
    embed.set_author(name=f"Channel information for {ch.name}.")

    # List current members in a voice channel.
    if ch.type == discord.ChannelType.voice and ch.members:
        mems = "\n".join([f'{str(mem)} ({mem.id})' for mem in ch.members])
        members = f"```{mems}```"
        field = [(f"Members: {len(ch.members)}", members, 0)]
        await emb_add_fields(embed, field)

    if ch.type == discord.ChannelType.category:
        if len(ch.channels) >= 1:
            valid = [chan for chan in ch.channels if chan.permissions_for(ctx.author).read_messages]
            chlist = ", ".join(chan.mention if chan.type == discord.ChannelType.text else chan.name for chan in valid)
            field = [(f"Channels under this category: {len(ch.channels)}", chlist, 0)]
            await emb_add_fields(embed, field)

    await ctx.reply(embed=embed)


@module.cmd("avatar",
            desc="Obtains the mentioned user's avatar, or your own.",
            aliases=["av"])
async def cmd_avatar(ctx: Context):
    """
    Usage```:
        {prefix}avatar [user]
    Description:
        Replies with the avatar of the provided user,
        or your own avatar if none was given.
    """
    user = ctx.author
    if ctx.arg_str != "":
        user = await ctx.find_member(ctx.arg_str, interactive=True)
        if not user:
            await ctx.reply("No matching users found!")
            return
    if str(user.colour) == "#000000":
        colour = ParaCC["blue"]
    else:
        colour = user.colour

    desc = f"Click [here]({user.avatar_url}) to view the {'GIF' if user.is_avatar_animated() else 'image'}."
    embed = discord.Embed(colour=colour, description=desc)
    embed.set_author(name="{}'s Avatar".format(user))
    embed.set_image(url=user.avatar_url)

    await ctx.reply(embed=embed)
