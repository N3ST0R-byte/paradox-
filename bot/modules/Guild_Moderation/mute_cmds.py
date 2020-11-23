import discord

from cmdClient.lib import ResponseTimedOut, UserCancelled

from wards import guild_moderator

from .module import guild_moderation_module as module

from . import mute_config  # noqa


# TODO: Muterole creation
@module.cmd("mute",
            desc="Silence a misbehaving user for a specified amount of time.",
            flags=['r==', 'f', 't=='],
            handle_edits=False)
@guild_moderator()
async def cmd_mute(ctx, flags):
    """
    Usage``:
        {prefix}mute user1, user2, user3, ... [-r <reason>] [-t <duration>]
    Description:
        Mutes the listed users with an optional reason.

        To use this command, you need to be a **guild moderator**.\
            That is, you need to have the `manage_guild` permission or the configured `modrole`.
        This command also requires that the `muterole` is\
            configured at `{prefix}config muterole`.
    Flags::
        ​r: (reason) Provide a reason for the mute (avoids the reason prompt).
        ​t: (time) Provide a duration for the mute, e.g. `1h 10m`.
    Examples``:
        {prefix}mute {ctx.author} -t 1d
    """
    if not ctx.args:
        return await ctx.error_reply("No arguments given, nothing to do.")

    # Give deprecation warning for -f
    if flags['f']:
        return await ctx.error_reply("The `f(ake)` flag is deprecated and will be removed in a future update.")

    # Handle duration
    if flags['t']:
        return await ctx.error_reply(
            "Apologies, timed mutes have been temporarily disabled, pending the next update."
        )

    # Check we have a mute role
    muterole = ctx.get_guild_setting.muterole.value
    if not muterole or not isinstance(muterole, discord.Role):
        return await ctx.error_reply(
            "No muterole set up! Please set `{}config muterole` before muting.".format(ctx.best_prefix())
        )

    # Get the reason
    reason = None
    if not flags['r']:
        # Interactively request the reason
        try:
            reason = await ctx.input("Please enter a reason for this mute, or `c` to cancel.")
        except ResponseTimedOut:
            raise ResponseTimedOut("Reason prompt timed out, cancelling mute.") from None
        if reason.lower() == 'c':
            raise UserCancelled("Moderator cancelled the reason prompt, cancelling mute.")
    else:
        reason = flags['r']

    if not reason:
        return await ctx.error_reply("No reason provided, cancelling mute.")

    users = []
    for userid in ctx.args.split(','):
        user = await ctx.find_member(userid.strip(), interactive=True)
        if user is None:
            return
        users.append(user)

    failed = []
    muted = []
    for user in users:
        try:
            await user.add_roles(muterole,
                                 reason="Muted by {}, reason {}".format(ctx.author, reason))
            muted.append(user)
        except discord.Forbidden:
            failed.append(user)
        except discord.HTTPException:
            failed.append(user)

    reports = []
    if muted:
        if len(muted) == 1:
            reports.append("Muted `{}`.".format(muted[0]))
        else:
            reports.append("Muted: `{}`.".format('`, `'.join(str(u) for u in muted)))
    if failed:
        if len(failed) == 1:
            reports.append("Failed to mute `{}`.".format(failed[0]))
        else:
            reports.append("Failed to mute: `{}`.".format('`, `'.join(str(u) for u in failed)))

    await ctx.reply('\n'.join(reports))
"""
# Check we have a muterole
# Check we can apply the muterole
# Go through the member searching process
# For each member to mute, do the following asynchronously:
    # Fire a mute process for the member:
        # If the member doesn't have the mute role, try to add it
        # If we fail here, the user is not muted and can't be muted. return False
        # Cancel any TimedMutes on the member, both cache and data
        # If there's a duration on the new mute, create a new TimedMute
        # Write the TimedMute to data
        # Start the task for the TimedMute
        # return
# We get a bunch of exceptions and return values here
# Use these to form the return string, dictating the mutes which succeeded and failed
"""


@module.cmd("unmute",
            desc="Unmute muted users.",
            flags=['r==', 'f'],
            handle_edits=False)
@guild_moderator()
async def cmd_unmute(ctx, flags):
    """
    Usage``:
        {prefix}unmute user1, user2, user3, ... [-r <reason>]
    Description:
        Unmutes the listed users with an optional reason.

        To use this command, you need to be a **guild moderator**.\
            That is, you need to have the `manage_guild` permission or the configured `modrole`.
        This command also requires that the `muterole` is\
            configured at `{prefix}config muterole`.
    Flags::
        ​r: (reason) Provide a reason for the unmute.
    Examples``:
        {prefix}unmute {ctx.author}
    """
    if not ctx.args:
        return await ctx.error_reply("No arguments given, nothing to do.")

    # Give deprecation warning for -f
    if flags['f']:
        return await ctx.error_reply("The `f(ake)` flag is deprecated and will be removed in a future update.")

    # Check we have a mute role
    muterole = ctx.get_guild_setting.muterole.value
    if not muterole or not isinstance(muterole, discord.Role):
        return await ctx.error_reply(
            "No muterole set up! Please set `{}config muterole` before unmuting.".format(ctx.best_prefix())
        )

    # Get the reason
    reason = flags['r'] if flags['r'] else None

    users = []
    for userid in ctx.args.split(','):
        user = await ctx.find_member(userid.strip(), interactive=True)
        if user is None:
            return
        users.append(user)

    failed = []
    muted = []
    for user in users:
        try:
            await user.remove_roles(muterole,
                                    reason="Unmuted by {}, reason {}".format(ctx.author, reason))
            muted.append(user)
        except discord.Forbidden:
            failed.append(user)
        except discord.HTTPException:
            failed.append(user)

    reports = []
    if muted:
        if len(muted) == 1:
            reports.append("UnMuted `{}`.".format(muted[0]))
        else:
            reports.append("UnMuted: `{}`.".format('`, `'.join(str(u) for u in muted)))
    if failed:
        if len(failed) == 1:
            reports.append("Failed to unmute `{}`.".format(failed[0]))
        else:
            reports.append("Failed to unmute: `{}`.".format('`, `'.join(str(u) for u in failed)))

    await ctx.reply('\n'.join(reports))
"""
# Check we have a muterole
# Check we can apply the muterole
# Go through the member searching process, only searching muted members maybe?
# For each member to unmute, do the following asynchronously:
    # Fire an unmute process for the member:
        # Cancel any TimedMutes on the member, both cache and data
        # If the member has the mute role, try to remove it
        # If we fail here, the user is not muted and can't be muted. return False
        # return
# We get a bunch of exceptions and return values here
# Use these to form the return string, dictating the mutes which succeeded and failed
"""
