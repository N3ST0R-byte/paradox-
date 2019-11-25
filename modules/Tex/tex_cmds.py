import discord
import asyncio
import os


from contextBot.Context import MessageContext as MCtx

from tex_config import show_config
from tex_compile import colourschemes
from tex_preamble import tex_pagination

from paraCH import paraCH

cmds = paraCH()

"""
Commands and handlers for LaTeX compilation, both manual and automatic.

Commands provided:
    texlisten:
        Toggles a user-setting for global tex recognition
    tex:
        Manually render LaTeX and configure rendering settings.

Handlers:
    tex_edit_listener:
        Listens to edited messages for automatic tex (re)compilation
    tex_listener:
        Listens to all new messages for automatic tex compilation

Initialisation:
    register_tex_listeners:
        Add all users and servers with tex listening enabled to bot objects

Bot Objects:
    user_tex_listeners: set of user id strings
    server_tex_listeners: dictionary of lists of math channel ids, indexed by server id
    latex_messages: dictionary of Contexts, indexed by message ids

User data:
    tex_listening: bool
        (app specific, user configured)
        Whether the user has global tex listening enabled
    latex_keepmsg: bool
        (app specific, user configured)
        Whether the latex source message will be deleted after compilation
    latex_colour: string
        (app specific, user configured)
        The background colour for compiled LaTeX output
    latex_alwaysmath: bool
        (app specific, user configured)
        Whether the `tex` command should render in paragraph or math mode
    latex_allowother: bool
        (app specific, user configured)
        Whether other users are allowed to use the showtex reaction on compiled output
    latex_showname: bool
        (app specific, user configured)
        Whether the user's name should be shown on the output
    latex_preamble: string
        (app independent, user configured)
        The preamble used in LaTeX compilation
    limbo-preamble: string
        (app independent, user configured)
        A preamble submitted by the user which is awaiting approval

Server data:
    maths_channels: list of channel ids
        (app specific, admin configured)
        The channels with automatic latex recognition enabled
    latex_listen_enabled: bool
        (app specific, admin configured)
        Whether automatic latex recognition is enabled at all
"""


@cmds.cmd("texlisten",
          category="Maths",
          short_help="Turns on listening to your LaTeX",
          aliases=["tl"])
async def cmd_texlisten(ctx):
    """
    Usage:
        {prefix}texlisten
    Description:
        Toggles listening to messages you post looking for tex.
        When tex is found, compiles it and replies to you.
    """
    listening = await ctx.data.users.get(ctx.authid, "tex_listening")

    # Add or remove the user from the current user tex listeners, and update the db entry
    if listening:
        ctx.bot.objects["user_tex_listeners"].discard(ctx.authid)
        await ctx.data.users.set(ctx.authid, "tex_listening", False)
        await ctx.reply("I have stopped listening to your tex.")
    else:
        ctx.bot.objects["user_tex_listeners"].add(ctx.authid)
        await ctx.data.users.set(ctx.authid, "tex_listening", True)
        await ctx.reply("I am now listening to your tex.")


def _is_tex(msg):
    """
    Helper to check whether an incoming or edited message contains LaTeX source code.
    """
    content = msg.clean_content
    is_tex = False

    # Check if there are an even number of dollar signs
    is_tex = is_tex or (("$" in content) and
                        1 - (content.count("$") % 2) and
                        content.strip("$"))

    # Check if it contains the start of an environment
    is_tex = is_tex or ("\\begin{" in content)

    # Check if it contains the \[ \] or \( \) math modes
    is_tex = is_tex or ("\\[" in content and "\\]" in content)
    is_tex = is_tex or ("\\(" in content and "\\)" in content)

    # If a non-latex code block exists, the message probably isn't LaTeX
    if is_tex and "```" in content and not any(word in content for word in ["```tex", "```latex", "```\n"]):
        # Check whether every such code block is a one liner, or has a space in the syntax field
        lines = content.splitlines()
        if not all(1 - line.count("```") % 2 or " " in line or line == "```" for line in lines if "```" in line):
            is_tex = False

    return is_tex


@cmds.cmd("tex",
          category="Maths",
          short_help="Renders LaTeX code",
          aliases=[",", "$", "$$", "align", "latex", "texw"])
@cmds.execute("flags", flags=["config", "keepmsg", "color==", "colour==", "alwaysmath", "allowother", "name"])
async def cmd_tex(ctx):
    """
    Usage:
        {prefix}tex <code>
        {prefix}, <code>
        {prefix}$ <equation>
        {prefix}$$ <displayeqn>
        {prefix}align <align block>
        {prefix}tex --colour white | black | grey | dark
    Description:
        Renders and displays LaTeX code.

        Using $ or , instead of tex compiles
        \\begin{{gather*}}<code>\\end{{gather*}}
        (You can treat this as a display equation with centering where \\\\ works.)

        Using $$ instead of tex compiles
        $$<code>$$.

        Using align instead of tex compiles
        \\begin{{align*}}<code>\\end{{align*}}.

        Use the reactions to delete the message and show your code, respectively.
    Flags:10
        config:: Shows you your current config.
        colour:: Changes your colourscheme. Run this as `--colour show` to see valid schemes
        keepmsg:: Toggles whether I delete your source message or not.
        alwaysmath:: Toggles whether {prefix}tex always renders in math mode.
        allowother:: Toggles whether other users may use the reaction to show your message source.
        name:: Toggles whether your name appears on the output message. Note the name of the image is your userid.
    Examples:
        {prefix}tex This is a fraction: $\\frac{{1}}{{2}}$
        {prefix}$ \\int^\\infty_0 f(x)~dx
        {prefix}$$ \\bmqty{{1 & 0 & 0\\\\ 0 & 1 & 0\\\\ 0 & 0 & 1}}
        {prefix}align a &= b\\\\ c &= d
        {prefix}tex --colour grey
    """
    if ctx.flags["config"]:
        await show_config(ctx)
        return
    elif ctx.flags["keepmsg"]:
        keepmsg = await ctx.data.users.get(ctx.authid, "latex_keep_message")
        if keepmsg is None:
            keepmsg = True
        keepmsg = 1 - keepmsg
        await ctx.data.users.set(ctx.authid, "latex_keep_message", keepmsg)
        if keepmsg:
            await ctx.reply("I will now keep your message after compilation.")
        else:
            await ctx.reply("I will not keep your message after compilation.")
        return
    elif ctx.flags["colour"] or ctx.flags["color"]:
        colour = ctx.flags["colour"] if ctx.flags["colour"] else ctx.flags["color"]
        if colour.lower() not in colourschemes.keys():
            await ctx.reply("Valid colour schemes are: `{}`".format("`, `".join(colourschemes.keys())))
            return
        await ctx.data.users.set(ctx.authid, "latex_colour", colour)
        await ctx.reply("Your colour scheme has been changed to {}".format(colour))
        return
    elif ctx.flags["alwaysmath"]:
        always = await ctx.data.users.get(ctx.authid, "latex_alwaysmath")
        if always is None:
            always = False
        always = 1 - always
        await ctx.data.users.set(ctx.authid, "latex_alwaysmath", always)
        if always:
            await ctx.reply("`{0}tex` will now render in math mode. You can use `{0}latex` to render normally.".format(ctx.used_prefix))
        else:
            await ctx.reply("`{0}tex` now render latex as usual.".format(ctx.used_prefix))
        return
    elif ctx.flags["allowother"]:
        allowed = await ctx.data.users.get(ctx.authid, "latex_allowother")
        if allowed is None:
            allowed = False
        allowed = 1 - allowed
        await ctx.data.users.set(ctx.authid, "latex_allowother", allowed)
        if allowed:
            await ctx.reply("Other people may now use the reaction to view your message source.")
        else:
            await ctx.reply("Other people may no longer use the reaction to view your message source.")
        return
    elif ctx.flags["name"]:
        showname = await ctx.data.users.get(ctx.authid, "latex_showname")
        if showname is None:
            showname = True
        showname = 1 - showname
        await ctx.data.users.set(ctx.authid, "latex_showname", showname)
        if showname:
            await ctx.reply("Your name is now shown on the output message.")
        else:
            await ctx.reply("Your name is no longer shown on the output message. Note that your user id appears in the name of the output image.")
        return

    # Handle empty input
    if ctx.arg_str == "":
        if ctx.used_cmd_name != ",":
            await ctx.reply("Please give me something to compile! See `{0}help` and `{0}help tex` for usage!".format(ctx.used_prefix))
        return

    # Set the messages compilation flags
    ctx.objs["latex_listening"] = False
    ctx.objs["latex_source_deleted"] = False
    ctx.objs["latex_out_deleted"] = False
    ctx.objs["latex_handled"] = True
    ctx.bot.objects["latex_messages"][ctx.msg.id] = ctx
    ctx.objs["latex_wide"] = (ctx.used_cmd_name == "texw")

    # Compile and send the final output message
    out_msg = await make_latex(ctx)

    # Start the reaction handler
    asyncio.ensure_future(reaction_edit_handler(ctx, out_msg), loop=ctx.bot.loop)

    # Hold the message context in cache for 600 seconds after the last edit or compilation
    if not ctx.objs["latex_source_deleted"]:
        ctx.objs["latex_edit_renew"] = False
        while True:
            await asyncio.sleep(600)
            if not ctx.objs["latex_edit_renew"]:
                break
            ctx.objs["latex_edit_renew"] = False
        ctx.bot.objects["latex_messages"].pop(ctx.msg.id, None)


async def parse_tex(ctx, source):
    """
    Extract the LaTeX source code to compile from a raw incoming message containing LaTeX.
    """
    if "```" in source:
        # TeX source with codeblocks gets treated specially.
        # Only the code in the codeblocks gets rendered.
        # We can assume here, from _is_tex, that there are no foreign codeblocks
        lines = source.splitlines()
        to_compile = []
        in_block = False
        for line in lines:
            if "```" in line:
                splits = line.split("```")
                for split in splits:
                    if in_block and split not in ["", "tex", "latex"]:
                        to_compile.append("{}\\\\".format(split))
                    in_block = not in_block
                if in_block:
                    to_compile.append("\\hfill\\break")
                in_block = not in_block
            elif in_block:
                to_compile.append(line)
        source = "\n".join(to_compile)

    # If the message starts and ends with backticks, strip them
    if source.startswith('`') and source.endswith('`'):
        source = source[1:-1]

    # If the message came from automatic recognition, don't change anything
    if ctx.objs["latex_listening"]:
        return source

    # Different compilation commands require different source wrappers
    always = await ctx.bot.data.users.get(ctx.authid, "latex_alwaysmath")
    if ctx.used_cmd_name in ["latex", "texw"] or (ctx.used_cmd_name == "tex" and not always):
        return source
    if ctx.used_cmd_name in ["$", ","] or (ctx.used_cmd_name == "tex" and always):
        return "\\begin{{gather*}}\n{}\n\\end{{gather*}}".format(source.strip(","))
    elif ctx.used_cmd_name == "$$":
        return "$${}$$".format(source)
    elif ctx.used_cmd_name == "align":
        return "\\begin{{align*}}\n{}\n\\end{{align*}}".format(source)
    else:
        return source


async def make_latex(ctx):
    """
    Compile LaTeX, send the output, and handle cleanup
    """
    # Strip the command header off the message if required
    source = ctx.msg.clean_content if ctx.objs["latex_listening"] else ctx.msg.clean_content.partition(ctx.used_cmd_name)[2].strip()
    ctx.objs["latex_source"] = await parse_tex(ctx, source)

    # Compile the source
    error = await texcomp(ctx)
    err_msg = ""

    # Check if the user wants to keep the source message
    keep = await ctx.data.users.get(ctx.authid, "latex_keep_message")
    keep = keep or (keep is None)

    # Make the error message if required
    # If there's no error and the user doesn't want to keep the source, delete it
    if error != "":
        err_msg = "Compile error! Output:\n```\n{}\n```".format(error)
    elif not keep:
        ctx.objs["latex_source_deleted"] = True
        await ctx.del_src()

    ctx.objs["latex_errmsg"] = err_msg

    # If the latex source is too long for in-channel display, set it to be dmmed.
    # In either case, build the display message.
    if len(ctx.objs["latex_source"]) > 1000:
        ctx.objs["dm_source"] = True
        ctx.objs["latex_source_msg"] = "```fix\nLaTeX source sent via direct message.\n```{}".format(err_msg)
    else:
        ctx.objs["dm_source"] = False
        ctx.objs["latex_source_msg"] = "```tex\n{}\n```{}".format(ctx.objs["latex_source"], err_msg)

    ctx.objs["latex_del_emoji"] = ctx.bot.objects["emoji_tex_del"]
    ctx.objs["latex_delsource_emoji"] = ctx.bot.objects["emoji_tex_delsource"]
    ctx.objs["latex_show_emoji"] = ctx.bot.objects["emoji_tex_errors" if error else "emoji_tex_show"]

    # Clean up the author's name and store it
    ctx.objs["latex_name"] = "**{}**:\n".format(ctx.author.name.replace("*", "\\*")) if (await ctx.data.users.get(ctx.authid, "latex_showname")) in [None, True] else ""

    # Send the final output, or a failure image if there is no output
    file_name = "tex/staging/{id}/{id}.png".format(id=ctx.authid)
    exists = True if os.path.isfile(file_name) else False
    out_msg = await ctx.reply(file_name=file_name if exists else "tex/failed.png",
                              message="{}{}".format(ctx.objs["latex_name"],
                                                    ("Compile Error! Click the {} reaction for details. (You may edit your message)".format(ctx.objs["latex_show_emoji"])) if error else ""))

    # Remove the output image and clean up
    if exists:
        os.remove(file_name)
    ctx.objs["latex_show"] = 0
    ctx.objs["latex_out_msg"] = out_msg
    return out_msg


async def reaction_edit_handler(ctx, out_msg):
    # Add the control reactions
    try:
        await ctx.bot.add_reaction(out_msg, ctx.objs["latex_del_emoji"])
        await ctx.bot.add_reaction(out_msg, ctx.objs["latex_show_emoji"])
        if not ctx.objs["latex_source_deleted"]:
            await ctx.bot.add_reaction(out_msg, ctx.objs["latex_delsource_emoji"])
    except discord.Forbidden:
        # If we can't react to the message or use external emojis, give up
        return
    allow_other = await ctx.bot.data.users.get(ctx.authid, "latex_allowother")

    # Build a check function to check if a reaction is valid
    def check(reaction, user):
        if user == ctx.me:
            return False
        result = reaction.emoji == ctx.objs["latex_del_emoji"] and user == ctx.author
        result = result or (reaction.emoji == ctx.objs["latex_show_emoji"] and (allow_other or user == ctx.author))
        result = result or (reaction.emoji == ctx.objs["latex_delsource_emoji"] and (user == ctx.author))
        return result

    # Loop around, waiting for valid reactions and handling them if they occur
    while True:
        res = await ctx.bot.wait_for_reaction(message=out_msg,
                                              timeout=300,
                                              check=check)
        if res is None:
            break
        if res.reaction.emoji == ctx.objs["latex_delsource_emoji"]:
            try:
                await ctx.bot.delete_message(ctx.msg)
            except discord.NotFound:
                pass
            except discord.Forbidden:
                pass
            try:
                await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_delsource_emoji"], ctx.me)
                await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_delsource_emoji"], ctx.author)
            except discord.NotFound:
                pass
            except discord.Forbidden:
                pass

        if res.reaction.emoji == ctx.objs["latex_del_emoji"] and res.user == ctx.author:
            await ctx.bot.delete_message(out_msg)
            ctx.objs["latex_out_deleted"] = True
            return
        if res.reaction.emoji == ctx.objs["latex_show_emoji"] and (res.user != ctx.me):
            try:
                await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_show_emoji"], res.user)
            except discord.Forbidden:
                pass
            except discord.NotFound:
                pass
            ctx.objs["latex_show"] = 1 - ctx.objs["latex_show"]
            await ctx.bot.edit_message(out_msg,
                                       "{}{} ".format(ctx.objs["latex_name"], (ctx.objs["latex_source_msg"] if ctx.objs["latex_show"] else "")))

            # If we need to show the source and dm, send it via the tex pager
            if ctx.objs["latex_show"] and ctx.objs["dm_source"]:
                pages = tex_pagination(ctx.objs["latex_source"], basetitle="LaTeX source", header=ctx.objs["latex_errmsg"])
                for page in pages:
                    page.set_author(name="Click here to jump back to message", url=ctx.msg_jumpto(out_msg))
                await ctx.pager(pages, embed=True, destination=res.user)

    # Remove the reactions and clean up
    try:
        await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_del_emoji"], ctx.me)
        await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_show_emoji"], ctx.me)
        await ctx.bot.remove_reaction(out_msg, ctx.objs["latex_delsource_emoji"], ctx.me)
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass


async def texcomp(ctx):
    """
    Put together the final configuration options for the LaTeX compilation, and compile
    """
    source = ctx.objs["latex_source"]
    preamble = await ctx.get_preamble()
    colour = await ctx.data.users.get(ctx.authid, "latex_colour")
    colour = colour if colour else "default"
    wide = ctx.objs.get("latex_wide", False)

    return await ctx.makeTeX(source, ctx.authid, preamble, colour, pad=not wide)


async def register_tex_listeners(bot):
    bot.objects["user_tex_listeners"] = set([str(userid) for userid in await bot.data.users.find("tex_listening", True, read=True)])
    bot.objects["server_tex_listeners"] = {}
    for serverid in await bot.data.servers.find("latex_listen_enabled", True, read=True):
        channels = await bot.data.servers.get(serverid, "maths_channels")
        bot.objects["server_tex_listeners"][str(serverid)] = channels if channels else []
    bot.objects["latex_messages"] = {}
    await bot.log("Loaded {} user tex listeners and {} server tex listeners.".format(len(bot.objects["user_tex_listeners"]), len(bot.objects["server_tex_listeners"])))


async def tex_listener(ctx):
    # Handle exit conditions
    if ctx.author.bot and int(ctx.authid) not in ctx.bot.bot_conf.getintlist("whitelisted_bots"):
        # No listening to non whitelisted bots
        return
    if "ready" not in ctx.bot.objects or not ctx.bot.objects["ready"]:
        # If we aren't initialised, fail silently
        return
    if "latex_handled" in ctx.objs and ctx.objs["latex_handled"]:
        # Message context already has had any latex processed
        return
    if ctx.server and (ctx.authid not in ctx.bot.objects["user_tex_listeners"]) and (ctx.server.id not in ctx.bot.objects["server_tex_listeners"]):
        # We are in a server, the user is not a listener, and the server is not a listener
        return
    if not _is_tex(ctx.msg):
        # The message doesn't contain any tex anyway
        return
    if ctx.server and (ctx.server.id in ctx.bot.objects["server_tex_listeners"]) and ctx.bot.objects["server_tex_listeners"][ctx.server.id] and not (ctx.ch.id in ctx.bot.objects["server_tex_listeners"][ctx.server.id]):
        # The current channel isn't in the list of math channels for the server
        return

    # Log the listening tex message
    if ctx.server:
        await ctx.bot.log("Recieved the following listening tex message from \"{ctx.author.name}\" in server \"{ctx.server.name}\":\n{ctx.cntnt}".format(ctx=ctx))
    else:
        await ctx.bot.log("Recieved the following listening tex message from \"{ctx.author.name}\" in DMS:\n{ctx.cntnt}".format(ctx=ctx))

    # Set the LaTeX compilation flags
    ctx.objs["latex_handled"] = True
    ctx.objs["latex_listening"] = True
    ctx.objs["latex_source_deleted"] = False
    ctx.objs["latex_out_deleted"] = False
    ctx.bot.objects["latex_messages"][ctx.msg.id] = ctx

    # Generate the LaTeX
    out_msg = await make_latex(ctx)

    ctx.objs["latex_out_msg"] = out_msg

    # Start the reaction handler
    asyncio.ensure_future(reaction_edit_handler(ctx, out_msg), loop=ctx.bot.loop)
    if not ctx.objs["latex_source_deleted"]:
        ctx.objs["latex_edit_renew"] = False
        while True:
            await asyncio.sleep(600)
            if not ctx.objs["latex_edit_renew"]:
                break
            ctx.objs["latex_edit_renew"] = False
        ctx.bot.objects["latex_messages"].pop(ctx.msg.id, None)


async def tex_edit_listener(bot, before, after):
    if before.id not in bot.objects["latex_messages"]:
        ctx = MCtx(bot=bot, message=after)
        await tex_listener(ctx)
        return
    ctx = bot.objects["latex_messages"][before.id]
    ctx.objs["latex_edit_renew"] = True
    ctx.msg = after

    old_out_msg = ctx.objs["latex_out_msg"] if "latex_out_msg" in ctx.objs else None
    if old_out_msg:
        try:
            await ctx.bot.delete_message(old_out_msg)
        except discord.NotFound:
            pass
    out_msg = await make_latex(ctx)
    asyncio.ensure_future(reaction_edit_handler(ctx, out_msg), loop=ctx.bot.loop)


def load_into(bot):
    bot.data.users.ensure_exists("tex_listening", "latex_keepmsg", "latex_colour", "latex_alwaysmath", "latex_allowother", "latex_showname", shared=False)
    bot.data.servers.ensure_exists("maths_channels", "latex_listen_enabled", shared=False)

    bot.add_after_event("ready", register_tex_listeners)
    bot.add_after_event("message_edit", tex_edit_listener)
    bot.after_ctx_message(tex_listener)
