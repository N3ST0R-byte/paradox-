from .module import guild_moderation_module as module

"""
Temporary blanks over the remaining moderation disabled for partial update.
"""


def temp_disabled(func):
    async def _func(ctx):
        """
        Sorry!:
            This command has been temporarily disabled pending the next update.
        """
        await ctx.error_reply(
            "Sorry, the `{}` command has been temporarily disabled pending the next update".format(
                func.__name__[4:]
            )
        )
    return _func


@module.cmd("hackban",
            desc="Pre-bans users who aren't in the guild by user id.",
            disabled=True)
@temp_disabled
async def cmd_hackban(ctx):
    pass


@module.cmd("ban",
            desc="Bans members of the guild and optionally purges their history.",
            disabled=True,)
@temp_disabled
async def cmd_ban(ctx):
    pass


@module.cmd("softban",
            desc="Bans and unbans members to 'kick and purge history'.",
            disabled=True)
@temp_disabled
async def cmd_softban(ctx):
    pass


@module.cmd("kick",
            desc="Kick users out of the guild.",
            disabled=True)
@temp_disabled
async def cmd_kick(ctx):
    pass


@module.cmd("unban",
            desc="Remove an active ban on a user.",
            disabled=True)
@temp_disabled
async def cmd_unban(ctx):
    pass


@module.cmd("giverole",
            desc="Give roles to a member.",
            disabled=True)
@temp_disabled
async def cmd_giverole(ctx):
    pass


@module.cmd("rolemod",
            desc="Give/take groups of roles to groups of members.",
            disabled=True)
@temp_disabled
async def cmd_rolemod(ctx):
    pass
