import discord
from datetime import datetime

from cmdClient import Context
from constants import ParaCC

from .module import meta_module as module

"""
Commands for users to give feedback on the bot.

Commands provided:
    feedback:
        Sends an embed containing user-submitted feedback to the feedback channel defined in the config.
"""
# TODO: Interactive bug reporting

# TODO: cooldown on feedback


@module.cmd("feedback",
            desc="Send feedback to my creators")
async def cmd_feedback(ctx: Context):
    """
    Usage``:
        {prefix}feedback <message>
    Description:
        Give feedback on anything regarding the bot, straight to the developers.
        This can be used for suggestions, bug reporting, or general feedback.
        Note that misuse of this command will lead to blacklisting.
    """
    response = ctx.arg_str
    if not response:
        response = await ctx.input("What message would you like to send? (`c` to cancel)", timeout=240)
        if response.lower() == "c":
            return await ctx.error_reply("Cancelled question.")
    embed = discord.Embed(title="Feedback", color=ParaCC["blue"], timestamp=datetime.now(), description=response)
    embed.set_author(name="{} ({})".format(ctx.author, ctx.author.id),
                     icon_url=ctx.author.avatar_url)
    embed.set_footer(text=datetime.utcnow().strftime("Sent from {}".format(ctx.guild.name if ctx.guild else "DM")))
    response = await ctx.ask("Are you sure you wish to send the above message to the developers?")
    if not response:
        return await ctx.error_reply("Cancelled feedback submission.")
    await ctx.client.objects["feedback_channel"].send(embed=embed)
    await ctx.reply("Thank you! Your feedback has been sent.\nConsider joining our support guild below to discuss your feedback with the developers and stay updated on the latest changes!\n{}".format(ctx.client.app_info["support_guild"]))
