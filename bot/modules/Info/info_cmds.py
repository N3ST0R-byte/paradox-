import discord
from cmdClient import Context
from wards import in_guild
from datetime import datetime
from utils.lib import emb_add_fields, paginate_list, strfdelta, prop_tabulate, format_activity, join_list
from constants import region_map, ParaCC
from discord import Status

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

    title = f"{role.name} ({role.id})"

    colour = role.colour if role.colour.value else discord.Colour.light_grey()
    num_users = len(role.members)
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
        position += "{:>4}.   {} {}\n".format(line_pos, ">" if guild_roles[line_pos]==role else " ", guild_roles[line_pos])
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

    members = role.members
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
    if ctx.arg_str:
        user = await ctx.find_member(ctx.arg_str, interactive=True)
        if not user:
            await ctx.reply("No matching users found!")
            return
    # Manually get a new user in case the old one was out of date
    user = await ctx.client.fetch_user(user.id)

    colour = (user.colour if user.colour.value else discord.Colour.light_grey())

    name = "{} {}".format(user, ctx.client.conf.emojis.getemoji("bot") if user.bot else "")

    statusnames = {
        Status.offline: "Offline",
        Status.dnd: "Do Not Disturb",
        Status.online: "Online",
        Status.idle: "Away",
    }

    # Acceptable statuses to be considered as active. 
    activestatus = [Status.online, Status.idle, Status.dnd]

    devicestatus = {
        "desktop": user.desktop_status in activestatus,
        "mobile": user.mobile_status in activestatus,
        "web": user.web_status in activestatus,
    }

    if any(devicestatus.values()):
        # String if the user is "online" on one or more devices.
        device = "Active on {}".format(join_list(string=[k for k,v in devicestatus.items() if v]))
    else:
        # String if the user isn't "online" on any device.
        device = "Not active on any device."

    activity = format_activity(user)
    presence = "{} {}".format(ctx.client.conf.emojis.getemoji(user.status.name), statusnames[user.status])
    numshared = sum(g.get_member(user.id) is not None for g in ctx.client.guilds)
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
    prop_list = ["Full name", "Nickname", "Presence", "Activity", "Device", "Usernames", "Nicknames", "Seen in", "Joined at", "", "Created at", ""]
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
        positions.append("{:>4}.   {} {}".format(line_pos + 1, ">" if joined[line_pos]==user else " ", joined[line_pos]))
    join_seq = "```markdown\n{}\n```".format("\n".join(positions))

    embed = discord.Embed(color=colour, description=desc)
    embed.set_author(name=f"{user} ({user.id})",
                     icon_url=user.avatar_url)
    embed.set_thumbnail(url=user.avatar_url)

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
    guild = ctx.guild

    if flags["icon"]:
        embed = discord.Embed(color=discord.Colour.light_grey())
        embed.set_image(url=guild.icon_url)
        return await ctx.reply(embed=embed)

    region = str(guild.region)
    region = region_map.get(region, region)

    verif_descs = {
        "none": "Unrestricted",
        "low": "Must have a verified email",
        "medium": "Must be registered for more than 5 minutes",
        "high": "Must be a member for more than 10 minutes",
        "extreme": "Must have a verified phone number",
    }

    verif_level = guild.verification_level.name
    ver = "{} | {}".format(verif_level.title(), verif_descs[verif_level])

    text = len(guild.text_channels)
    voice = len(guild.voice_channels)
    category = len(guild.categories)
    total = len(guild.channels)

    statuses = [s for s in Status if s!=Status.invisible]
    activestatus = [s for s in statuses if s!=Status.offline]
    emoji = {s: ctx.client.conf.emojis.getemoji(s.name) for s in statuses}

    counts = {s:0 for s in statuses}
    desktop = mobile = web = 0

    for m in guild.members:
        counts[m.status] += 1

        desktop += m.desktop_status in activestatus
        mobile += m.mobile_status in activestatus
        web += m.web_status in activestatus

    status = '\n'.join("{} - **{}**".format(emoji[s], counts[s]) for s in statuses)
    devicestatus = "🖥️ - **{}**\n📱 - **{}**\n🌎 - **{}**".format(desktop, mobile, web)

    bots = sum(m.bot for m in guild.members)
    members = "{} humans, {} bots | {} total".format(guild.member_count - bots,
                                                     bots, guild.member_count)

    owner = "{0} ({0.id})".format(guild.owner)                                                 
    icon = "[Icon Link]({})".format(guild.icon_url)
    is_large = ("More" if guild.large else "Less")+ " than 250 members"
    mfa = "Enabled" if guild.mfa_level else "Disabled"
    channels = "{} text, {} voice, {} categories | {} total".format(text, voice, category, total)
    boosts = "Level {} | {} boosts total".format(guild.premium_tier, guild.premium_subscription_count)
    created = guild.created_at.strftime("%I:%M %p, %d/%m/%Y")
    created_ago = "({} ago)".format(strfdelta(datetime.utcnow() - guild.created_at, minutes=False))

    prop_list = ["Owner", "Region", "Icon", "Large server?", "Verification", "2FA", "Roles", "Members", "Channels", "Server Boosts", "Created at", ""]
    value_list = [owner,
                  region,
                  icon,
                  is_large,
                  ver,
                  mfa,
                  len(guild.roles),
                  members, channels, boosts, created, created_ago]
    desc = prop_tabulate(prop_list, value_list)

    embed = discord.Embed(color=guild.owner.colour if guild.owner.colour.value else discord.Colour.teal(), description=desc)
    embed.set_author(name="{0} ({0.id})".format(ctx.guild))
    embed.set_thumbnail(url=guild.icon_url)

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

    # Disallow selecting channels that the user cannot see. Channels the bot can see still work.
    valid_channels = [ch for ch in ctx.guild.channels if ch.permissions_for(ctx.author).read_messages]
    if not ctx.arg_str:
        ch = ctx.ch
    else:
        ch = await ctx.find_channel(ctx.arg_str, interactive=True, collection=valid_channels)
        if not ch:
            return
    # Generic embed info, valid for every channel type. 
    name = f"{ch.name} [{ch.mention}]" if isinstance(ch, discord.TextChannel) else f"{ch.name}"
    created = ch.created_at.strftime("%d/%m/%Y")
    created_ago = f"({strfdelta(datetime.utcnow() - ch.created_at, minutes=True)} ago)"

    category = "{0} ({0.id})".format(ch.category) if ch.category else "None"

    # Embed info specific to text channels.
    if isinstance(ch, discord.TextChannel):
        topic = ch.topic or "No topic."
        nsfw = "Yes" if ch.nsfw else "No"
        prop_list = ["Name", "Type", "ID", "NSFW", "Category", "Created at", "", "Topic"]
        value_list = [name, tv[str(ch.type)], ch.id, nsfw, category, created, created_ago, topic]

    # Embed info specific to voice channels.
    elif isinstance(ch, discord.VoiceChannel):
        userlimit = ch.user_limit or "Unlimited"

        prop_list = ["Name", "Type", "ID", "Category", "Created at", "", "User limit"]
        value_list = [name, tv[str(ch.type)], ch.id, category, created, created_ago, userlimit]

    # If any other type is present, provide generic information only.
    else:
        prop_list = ["Name", "Type", "ID", "Created at", ""]
        value_list = [name, tv[str(ch.type)], ch.id, created, created_ago]

    desc = prop_tabulate(prop_list, value_list)
    embed = discord.Embed(color=ParaCC["blue"], description=desc)
    embed.set_author(name=f"Channel information for {ch.name}.")

    # List current members in a voice channel.
    if isinstance(ch, discord.VoiceChannel) and ch.members:
        mems = "\n".join(f'{mem} ({mem.id})' for mem in ch.members)
        members = f"```{mems}```"
        field = [(f"Members: {len(ch.members)}", members, 0)]
        await emb_add_fields(embed, field)

    # List visible channels in a category
    if isinstance(ch, discord.CategoryChannel):
        valid = [chan for chan in ch.channels if chan.permissions_for(ctx.author).read_messages]
        if valid:
            chlist = ", ".join(chan.mention if isinstance(chan, discord.TextChannel) else chan.name for chan in valid)
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
    embed.set_author(name=f"{user}'s Avatar")
    embed.set_image(url=user.avatar_url)

    await ctx.reply(embed=embed)
