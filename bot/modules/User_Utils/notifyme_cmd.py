from .module import utils_module as module


@module.cmd("notifyme",
            desc="DMs you messages matching given triggers.",
            aliases=["tellme", "pounce", "listenfor", "notify"])
async def cmd_notifyme(ctx):
    """
    Sorry!:
        **This feature has been temporarily disabled pending the next update.**
    """
    await ctx.error_reply(
        "Sorry, the `notifyme` system has been temporarily disabled pending the next updates."
    )
