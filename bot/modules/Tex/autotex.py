import asyncio

from cmdClient import cmdClient

from .module import latex_module as module

from .core.LatexUser import LatexUser
from .core.LatexGuild import LatexGuild
from .core.LatexContext import LatexContext
from .core.tex_utils import ParseMode, AutoTexLevel


async def latex_message_parser(client, message):
    """
    Check incoming messages for LaTeX, render them if required, and add them to cache.
    As a cmdClient message parser, it handles both new messages and edits which were ignored by the command parser.
    """
    # Quit if module has been disabled
    if not module.enabled:
        return

    # Wait until module is ready
    while not module.ready:
        await asyncio.sleep(1)

    # TODO: Handle whitelisted bots
    if message.author.bot:
        return

    # Make sure there's content
    if not message.content:
        return

    # TODO: Handle blacklisted users and guilds

    # Get the latex guild
    lguild = LatexGuild.get(message.guild.id if message.guild else 0)

    # Check we can write in the channel and we're allowed to send latex there
    if message.guild:
        my_permissions = message.channel.permissions_for(message.guild.me)
        if not (my_permissions.send_messages and my_permissions.attach_files):
            return

        if lguild.latex_channels:
            if message.channel.id not in lguild.latex_channels:
                return

    # If the guild requires codeblocks, check now
    if lguild.require_codeblocks and "```" not in message.content:
        return

    # Build the potential latex source
    source = LatexContext.parse_content(message.clean_content, ParseMode.DOCUMENT)

    # Check what latex level we have, if any
    if ("```tex" in message.content) or ("```latex" in message.content):
        level = AutoTexLevel.CODEBLOCK
    elif LatexContext.strict_hastex(source):
        level = AutoTexLevel.STRICT
    elif LatexContext.weak_hastex(source):
        level = AutoTexLevel.WEAK
    else:
        # The message doesn't contain any latex, return now
        return

    # Check whether our latex level is high enough for the guild
    if level < lguild.autotex_level:
        return

    # We are now in the (relatively rare) case that a message seems to have LaTeX.
    # Build the latex user
    luser = LatexUser.get(message.author.id)

    # Check whether our latex level is high enough for the user
    if level < luser.autotex_level:
        return

    # Final check of whether we are listening, now that we have everything
    if not (lguild.autotex or luser.autotex):
        return

    # We have a valid piece of LaTeX, and we are listening for it. We may now compile.
    # TODO: Log

    # First create a context for the message and add it to the context caches
    ctx = client.baseContext(client=client, message=message)
    client.ctx_cache[message.id] = ctx.flatten()
    client.active_contexts[message.id] = ctx

    try:
        # Create the LatexContext
        # TODO: More options
        lctx = LatexContext(ctx, source, lguild=lguild, luser=luser)

        # Compile the source
        await lctx.make()

        # Wait for the context to deactivate
        await lctx.lifetime()
    except Exception as e:
        # TODO: Log
        raise e
    finally:
        client.ctx_cache[message.id] = ctx.flatten()
        client.active_contexts.pop(message.id, None)


@module.init_task
def register_latex_parser(client: cmdClient):
    client.add_message_parser(latex_message_parser)
