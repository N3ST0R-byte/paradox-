import discord
from enum import Enum


class ActionState(Enum):
    """
    Final state of a mute action (i.e. muting or unmuting).
    """
    INTERNAL_UNKNOWN = -1  # Unknown internal error occurred
    SUCCESS = 0  # Successfully completed the action
    MEMBER_NOTFOUND = 1  # Couldn't find the member
    FORBIDDEN = 2  # Couldn't modify the user
    GUILD_NOTFOUND = 3  # Couldn't find the guild


async def _find_member(guild, memberid):
    """
    Attempt to retrieve a member.
    Either returns the member, None, or throws a Discord exception.
    """
    # Attempt the find the member
    member = guild.get_member(memberid)
    if not member:
        member = await guild.fetch_member(memberid)
    return member


async def mute_member(guild, muterole, member, audit_reason=None):
    """
    Mute a member of the given guild, given a member object.
    """
    # Attempt to add the mute role
    try:
        await member.add_roles(muterole, reason=audit_reason)
    except discord.Forbidden:
        return ActionState.FORBIDDEN
    except discord.HTTPException:
        return ActionState.INTERNAL_UNKNOWN
    else:
        return ActionState.SUCCESS


async def mute_memberid(guild, muterole, memberid, audit_reason=None):
    """
    Attempt to mute a single member of the given guild by id.
    """
    # Get the member
    try:
        member = await _find_member(guild, memberid)
    except discord.Forbidden:
        return ActionState.GUILD_NOTFOUND
    except discord.HTTPException:
        return ActionState.MEMBER_NOTFOUND
    if member is None:
        return ActionState.MEMBER_NOTFOUND

    return await mute_member(member)


async def unmute_member(guild, muterole, memberid, audit_reason=None):
    """
    Attempt to unmute a single member of the given guild.
    """
    # Get the member
    try:
        member = await _find_member(guild, memberid)
    except discord.Forbidden:
        return ActionState.GUILD_NOTFOUND
    except discord.HTTPException:
        return ActionState.MEMBER_NOTFOUND
    if member is None:
        return ActionState.MEMBER_NOTFOUND

    # Attempt to remove the mute role
    try:
        await member.remove_roles(muterole, reason=audit_reason)
    except discord.Forbidden:
        return ActionState.FORBIDDEN
    except discord.HTTPException:
        return ActionState.INTERNAL_UNKNOWN
    else:
        return ActionState.SUCCESS
