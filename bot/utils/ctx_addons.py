import asyncio
import logging

import discord
from cmdClient import Context

import logger


@Context.util
async def embedreply(ctx, desc, colour=discord.Colour(0x9b59b6), **kwargs):
    """
    Simple helper to embed replies.
    All arguments are passed to the embed constructor.
    `desc` is passed as the `description` kwarg.
    """
    embed = discord.Embed(description=desc, colour=colour, **kwargs)
    return await ctx.reply(embed=embed)


@Context.util
async def live_reply(ctx, reply_func, update_interval=5, max_messages=20):
    """
    Acts as `ctx.reply`, but asynchronously updates the reply every `update_interval` seconds
    with the value of `reply_func`, until the value is `None`.

    Parameters
    ----------
    reply_func: coroutine
        An async coroutine with no arguments.
        Expected to return a dictionary of arguments suitable for `ctx.reply()` and `Message.edit()`.
    update_interval: int
        An integer number of seconds.
    max_messages: int
        Maximum number of messages in channel to keep the reply live for.

    Returns
    -------
    The output message after the first reply.
    """
    # Send the initial message
    message = await ctx.reply(**(await reply_func()))

    # Start the counter
    future = asyncio.ensure_future(_message_counter(ctx.client, ctx.ch, max_messages))

    # Build the loop function
    async def _reply_loop():
        while not future.done():
            await asyncio.sleep(update_interval)
            args = await reply_func()
            if args is not None:
                await message.edit(**args)
            else:
                break

    # Start the loop
    asyncio.ensure_future(_reply_loop())

    # Return the original message
    return message


async def _message_counter(client, channel, max_count):
    """
    Helper for live_reply
    """
    # Build check function
    def _check(message):
        return message.channel == channel

    # Loop until the message counter reaches maximum
    count = 0
    while count < max_count:
        await client.wait_for('message', check=_check)
        count += 1
    return


@Context.util
def log(ctx: Context, *args, **kwargs):
    """
    Shortcut to the logger which automatically adds the context.
    """
    if "context" not in kwargs:
        kwargs['context'] = "mid:{}".format(ctx.msg.id)
    logger.log(*args, **kwargs)


@Context.util
async def run_in_shell(ctx: Context, script):
    """
    Execute a script or command asynchronously in a subprocess shell.
    """
    process = await asyncio.create_subprocess_shell(script, stdout=asyncio.subprocess.PIPE)
    ctx.log(
        "Executing the following script:\n{}\nwith pid '{}'.".format(
            "\n".join("\t{}".format(line) for line in script.splitlines()),
            process.pid
        )
    )
    stdout, stderr = await process.communicate()
    ctx.log("Completed the script with pid '{}'{}".format(
        process.pid,
        " with errors" if process.returncode != 0 else ""),
        level=logging.DEBUG
    )
    return stdout.decode(errors='backslashreplace').strip()


@Context.util
def best_prefix(ctx: Context):
    """
    Returns the best default prefix in the current context.
    This will be the server prefix if it is defined,
    otherwise the default client prefix.
    """
    if ctx.guild:
        prefix = ctx.client.objects["guild_prefix_cache"].get(ctx.guild.id, ctx.client.prefix)
    else:
        prefix = ctx.client.prefix
    return prefix


@Context.util
def format_usage(ctx: Context):
    """
    Formats the usage string of the current command.
    Assumes the first section of the doc string is the usage string.
    """
    usage = ctx.cmd.long_help[0][1]
    usage = usage.format(ctx=ctx, client=ctx.client, prefix=ctx.best_prefix())
    return "**USAGE:**{}{}".format(
        '\n' if '\n' in usage else ' ',
        usage
    )


@Context.util
async def confirm_sent(ctx: Context, msg=None, reply=None):
    """
    Confirms to a user that the bot has DMed them by adding a tick reaction to the command message.
    If the bot doesn't have permission to add reactions, it will respond with a message if reply is provided.
    Parameters
    ----------
    msg: Message
        The message to add the reaction to, otherwise assumes ctx.msg.
    reply: str
        A custom response to confirm the message has been sent, if the bot lacks permission to add reactions.
    """
    try:
        if not msg:
            await ctx.msg.add_reaction("✅")
        else:
            await msg.add_reaction("✅")
    except discord.Forbidden:
        return await ctx.reply(reply if reply else "Check your DMs!")


@Context.util
async def offer_delete(ctx: Context, msg, *to_delete):
    """
    Offers to delete the output message by adding a reaction.

    Parameters
    ----------
    msg: Message
        The output message to offer to delete.
    to_delete: list(Message):
        Multiple messages to delete if the user reacts.
    """
    emoji = ctx.client.conf.emojis.getemoji("delete")

    if msg is None and to_delete is None:
        return

    # !!! Needs updating for rewrite !!! #
    # mod_role = await ctx.server_conf.mod_role.get(ctx) if ctx.server else None
    mod_role = None

    if ctx.guild:
        def check(reaction, user):
            # !!! Needs updating for rewrite !!! #
            """
            if user == ctx.client.user:
                return False
            result = user == ctx.author           
            result = result or (mod_role and mod_role in [role.id for role in user.roles])
            result = result or user.server_permissions.administrator
            result = result or user.server_permissions.manage_messages
            """
            return user == ctx.author and msg == msg and reaction.emoji == emoji
    else:
        def check(reaction, user):
            return user == ctx.author and msg == msg and reaction.emoji == emoji
    try:
        await msg.add_reaction(emoji)
    except discord.Forbidden:
        return

    try:
        reaction, user = await ctx.client.wait_for("reaction_add", check=check, timeout=300)
        if reaction.emoji == emoji:
            to_delete = to_delete if to_delete is not None else [msg]
            for m in to_delete:
                try:
                    await m.delete()
                except Exception:
                    pass
    except asyncio.TimeoutError:
        try:
            await msg.remove_reaction(emoji, ctx.client.user)
        except Exception:
            pass
