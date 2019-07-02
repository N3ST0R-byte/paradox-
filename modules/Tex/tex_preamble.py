import os
import asyncio
import aiohttp
from datetime import datetime
from io import StringIO

import discord

from paraCH import paraCH

cmds = paraCH()

"""
Handle LaTeX preamble submission and approval/processing

Commands:
    preamble: User command to show or modify their preamble
    serverpreamble: Server command to show or modify server default preamble
    preambleadmin: Bot admin command to manage preamble submissions and individual preambles
"""


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, "preamble.tex"), 'r') as preamble:
    default_preamble = preamble.read()


def split_text(text, blocksize, code=True, syntax="", maxheight=50):
    # Break the text into blocks of maximum length blocksize
    # If possible, break across nearby newlines. Otherwise just break at blocksize chars
    blocks = []
    while True:
        if len(text) <= blocksize:
            blocks.append(text)
            break

        split_on = text[0:blocksize].rfind('\n')
        split_on = blocksize if split_on == -1 else split_on

        blocks.append(text[0:split_on])
        text = text[split_on:]

    # Add the codeblock ticks and the code syntax header, if required
    if code:
        blocks = ["```{}\n{}\n```".format(syntax, block) for block in blocks]

    return blocks


def tex_pagination(text, basetitle="", header=None, timestamp=True, colour=discord.Colour.dark_blue()):
    blocks = split_text(text, 1000, code=True, syntax="tex")

    blocknum = len(blocks)

    if blocknum == 1:
        return [discord.Embed(title=basetitle,
                              color=colour,
                              description=blocks[0],
                              timestamp=datetime.utcnow())]

    embeds = []
    for i, block in enumerate(blocks):
        desc = "{}\n{}".format(header, block) if header else block
        embed = discord.Embed(title=basetitle,
                              colour=colour,
                              description=desc,
                              timestamp=datetime.utcnow())
        embed.set_footer(text="Page {}/{}".format(i+1, blocknum))
        embeds.append(embed)

    return embeds


async def sendfile_reaction_handler(ctx, out_msg, temp_file, title):
    try:
        await ctx.bot.add_reaction(out_msg, ctx.bot.objects["emoji_sendfile"])
    except discord.Forbidden:
        return

    while True:
        res = await ctx.bot.wait_for_reaction(message=out_msg,
                                              emoji=ctx.bot.objects["emoji_sendfile"],
                                              timeout=300)
        if res is None:
            try:
                await ctx.bot.remove_reaction(out_msg, ctx.bot.objects["emoji_sendfile"], ctx.me)
            except Exception:
                pass
            break
        elif res.user != ctx.me:
            try:
                await ctx.bot.send_file(res.user, fp=temp_file, filename="preamble.tex", content=title)
            except discord.Forbidden:
                await ctx.reply("Sorry, I tried to DM the preamble file, but couldn't reach you!")
            except discord.HTTPException:
                pass
            try:
                await ctx.bot.remove_reaction(out_msg, ctx.bot.objects["emoji_sendfile"], res.user)
            except Exception:
                pass


async def view_preamble(ctx, preamble, title, header=None, file_react=False, file_message=None):
    pages = tex_pagination(preamble, basetitle=title, header=header)
    out_msg = await ctx.pager(pages, embed=True, locked=False)

    if not file_react or out_msg is None:
        return out_msg

    # Generate file to send to user on reaction press
    with StringIO() as temp_file:
        temp_file.write(preamble)
        temp_file.seek(0)
        asyncio.ensure_future(sendfile_reaction_handler(ctx, out_msg, temp_file, file_message or title))

    return out_msg


async def confirm(ctx, question, preamble, **kwargs):
    out_msg = await view_preamble(ctx, preamble, "{} (y/n)".format(question), **kwargs)
    result_msg = await ctx.listen_for(["y", "yes", "n", "no"], timeout=120)

    if result_msg is None:
        return None
    result = result_msg.content.lower()
    try:
        await ctx.bot.delete_message(out_msg)
        await ctx.bot.delete_message(result_msg)
    except Exception:
        pass
    if result in ["n", "no"]:
        return False
    return True


async def preamblelog(ctx, title, user=None, source=None):
    """
    Log a message to the preamble log channel
    """
    pass


async def test_preamble(ctx, preamble):
    """
    Test preamble code in a preamble channel
    """
    pass


async def handled_preamble(ctx, userid, info):
    """
    Clean up after a preamble submission request has been handled
    """
    pass


async def submit_preamble(ctx, user, submission, info):
    """
    Make a new preamble submission
    """
    # If there is a previous active request, mark it as outdated
    old_sub = await ctx.data.users.get(user.id, "pending_preamble")
    if old_sub:
        await handled_preamble(ctx, user.id, "New preamble request submitted")

    # Set the new pending preamble
    await ctx.data.users.set(ctx.authid, "pending_preamble", submission)

    # Send the preamble request to the submission channel
    submission_channel = ctx.bot.objects["latex_preamble_subch"]
    newctx = ctx.bot.make_msgctx(channel=submission_channel)
    title = "Preamble submission from {}({}) at {}".format(user, user.id, datetime.utcnow())
    sub_msg = await view_preamble(newctx, submission, title, header=info)

    # Store the pending preamble info
    info_pack = (title, info, sub_msg.id)
    await ctx.data.users.set(ctx.authid, "pending_preamble_info", info_pack)

    # Add or update the pending preamble in the cached list
    ctx.bot.objects["pending_preambles"][user.id] = (submission, info_pack)

    # Add the approval/denial/testing emojis to the submission
    asyncio.ensure_future(judgement_reactions(newctx, user.id, sub_msg))


async def judgement_reactions(ctx, userid, msg):
    approve_emo = ctx.bot.objects["emoji_approve"]
    deny_emo = ctx.bot.objects["emoji_deny"]
    test_emo = ctx.bot.objects["emoji_test"]

    def judgement_check(reaction, user):
        return (reaction.emoji in [approve_emo, deny_emo, test_emo]) and ctx.is_manager(user)

    try:
        await ctx.bot.add_reaction(msg, approve_emo)
        await ctx.bot.add_reaction(msg, deny_emo)
        await ctx.bot.add_reaction(msg, test_emo)
    except discord.Forbidden:
        return

    while True:
        res = await ctx.bot.wait_for_reaction(message=msg,
                                              check=judgement_check,
                                              timeout=600)
        if res is None:
            if userid in ctx.bot.objects["pending_preambles"]:
                continue
            try:
                await ctx.bot.remove_reaction(msg, approve_emo, ctx.me)
                await ctx.bot.remove_reaction(msg, deny_emo, ctx.me)
                await ctx.bot.remove_reaction(msg, test_emo, ctx.me)
            except Exception:
                pass
            break
        if res.reaction.emoji == approve_emo:
            if await approve_submission(ctx, userid, res.user):
                break
        elif res.reaction.emoji == deny_emo:
            if await deny_submission(ctx, userid, res.user):
                break
        elif res.reaction.emoji == test_emo:
            await test_submission(ctx, userid, res.user)


async def approve_submission(ctx, userid, manager):
    ctx.author = manager  # Hack so that ask and input work properly

    # First update the preamble
    current_preamble = await ctx.data.users.get(userid, "latex_preamble")
    await ctx.data.users.set(userid, "previous_preamble", current_preamble)

    new_preamble = await ctx.data.users.get(userid, "pending_preamble")
    await ctx.data.users.set(userid, "latex_preamble", new_preamble)

    await ctx.data.users.set(userid, "pending_preamble", None)
    await ctx.data.users.set(userid, "pending_preamble_info", None)
    ctx.bot.objects["pending_preambles"].pop(userid)

    # Then mark the case as handled
    await handled_preamble(ctx, userid, "Preamble approved by {}".format(manager.mention))

    # Find the user
    user = await ctx.find_user(userid, in_server=False, interactive=True)
    if not user:
        await ctx.reply("Couldn't find the user to DM them!")
    else:
        # Create default approval message
        default_msg = "{}, your recent request for a LaTeX preamble submission has been approved!\
            \nYour preamble has been modified and may be seen using the `preamble` command.\
            \nShould you wish to revert these changes, please use `preamble --revert`.".format(user.name)
        embed = discord.Embed(title="Preamble request approval", description=default_msg)
        embed.timestamp = datetime.utcnow()

        # Check whether this needs editing
        default_reply = await ctx.reply(embed=embed)
        result = await ctx.ask("Do you wish to edit the approval message? (Auto-sending in 20s)", timeout=20, del_on_timeout=True)
        if result:
            result = await ctx.input("Please enter the new approval message!", timeout=600)
            if not result:
                await ctx.reply("Query timed out, sending default message.")
            else:
                embed.description = result
        await ctx.bot.delete_message(default_reply)

        # Try and DM the user with their happy news
        try:
            await ctx.send(user, embed=embed)
        except discord.Forbidden:
            await ctx.reply("I wasn't allowed to DM this user.. they might have me blocked")
        except Exception:
            await ctx.reply("Something unknown went wrong while DMMing this user!")


async def deny_submission(ctx, userid, manager):
    ctx.author = manager  # Hack so that ask and input work properly

    # Find the user
    user = await ctx.find_user(userid, in_server=False, interactive=True)
    if not user:
        await ctx.reply("Couldn't find the user to DM them!")
    else:
        # Query for the denial message
        result = await ctx.input("Please enter the reason this request was denied, or `c` to cancel", timeout=600)
        if not result:
            await ctx.reply("Timed out waiting for a rejection reason, aborting preamble request rejection!")
            return
        if result.lower() == 'c':
            await ctx.reply("Aborting preamble rejection on manager request!")
            return
        embed = discord.Embed(title="Unfortunately, your preamble request was denied!", description=result)
        embed.timestamp = datetime.utcnow()

        # Try and DM the user
        try:
            await ctx.send(user, embed=embed)
        except discord.Forbidden:
            await ctx.reply("I wasn't allowed to DM this user.. they might have me blocked")
        except Exception:
            await ctx.reply("Something unknown went wrong while DMMing this user!")

    # Deny the submission
    await ctx.data.users.set(userid, "pending_preamble", None)
    await ctx.data.users.set(userid, "pending_preamble_info", None)
    ctx.bot.objects["pending_preambles"].pop(userid)

    # Then mark the case as handled
    await handled_preamble(ctx, userid, "Preamble denied by {}".format(manager.mention))


async def test_submission(ctx, userid):
    # Not implemented
    pass


@cmds.cmd("showpreamble",
          category="Maths",
          short_help="View or modify your LaTeX preamble",
          flags=['reset', 'retract', 'add', 'remove', 'revert', 'usepackage', 'replace'])
async def cmd_showpreamble(ctx):
    """
    Usage:
        Magick
    """
    # Handle resetting the preamble
    if ctx.flags["reset"]:
        resp = await ctx.ask("Are you sure you want to reset your preamble to the default?", timeout=60)
        if resp:
            # Reset the preamble
            current_preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")

            await ctx.data.users.set(ctx.authid, "previous_preamble", current_preamble)
            await ctx.data.users.set(ctx.authid, "latex_preamble", None)
            await ctx.data.users.set(ctx.authid, "pending_preamble", None)
            await ctx.data.users.set(ctx.authid, "pending_preamble_info", None)
            ctx.bot.objects["pending_preambles"].pop(ctx.authid)
            await ctx.reply("Your preamble has been reset!")

            await handled_preamble(ctx, ctx.authid, "Preamble was reset")
            await preamblelog(ctx, "Preamble has been reset to the default")
        else:
            await ctx.reply("Aborting...")
        return

    # Handle retracting a preamble request
    if ctx.flags["retract"]:
        await ctx.data.users.set(ctx.authid, "pending_preamble", None)
        await ctx.data.users.set(ctx.authid, "pending_preamble_info", None)
        ctx.bot.objects["pending_preambles"].pop(ctx.authid)

        await ctx.reply("Your preamble request has been retracted!")
        await handled_preamble(ctx, ctx.authid, "Request retracted")
        await preamblelog(ctx, "Preamble request was retracted")
        return

    # Handle reverting to the previous version of the preamble
    if ctx.flags["revert"]:
        resp = await ctx.ask("Are you sure you want to revert your preamble to the previous version?", timeout=60)
        if resp:
            previous_preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
            if not previous_preamble:
                await ctx.reply("Your previous preamble doesn't exist or wasn't recorded!")
            else:
                current_preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")

                await ctx.data.users.set(ctx.authid, "previous_preamble", current_preamble)
                await ctx.data.users.set(ctx.authid, "latex_preamble", previous_preamble)

                await ctx.reply("Your preamble has been reverted.")
                await preamblelog(ctx, "Preamble was reverted to the previous version")
        else:
            await ctx.reply("Aborting...")
        return

    header = None

    # Get the current active preamble and set the header for viewing
    preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
    if not preamble and ctx.server:
        preamble = await ctx.data.servers.get(ctx.server.id, "server_latex_preamble")
        header = "No custom user preamble set, server preamble."
    if not preamble:
        preamble = default_preamble
        header = "No custom user preamble set, using default preamble."

    # Get any input, including the contents of any attached files if they exist
    if ctx.msg.attachments:
        file_info = ctx.msg.attachments[0]

        # If the file is over 1MB, it probably isn't a valid preamble.
        if file_info['size'] >= 1000000:
            await ctx.reply("Attached file is too large to process.")
            return

        async with aiohttp.get(file_info['url']) as r:
            new_source = await r.text()
    else:
        new_source = ctx.arg_str

    # Handle a request to remove material from the preamble
    if ctx.flags['remove']:
        to_remove = []  # List of line indicies to remove
        new_preamble = None
        lines = preamble.splitlines()

        # If arguments were given, search the current preamble for this string
        if new_source:
            if new_source not in preamble:
                await ctx.reply("The requested text doesn't appear in any line of your preamble!")
                return
            if '\n' in new_source:
                # If the requested string has multiple lines and appears, just remove all of them
                new_preamble = preamble.replace(new_source, "")
            else:
                # Otherwise, make a list of matching lines to remove
                to_remove = [i for i, line in enumerate(lines) if new_source in line]
        else:
            # If we aren't given anything to remove, prompt the user for which lines they want to remove
            # Generate a version of the current preamble with line numbers
            lined_preamble = "\n".join(("{:>2}. {}".format(i, line) for i, line in enumerate(lines)))

            # Show this to the user and prompt them
            prompt = "Please enter the line numbers to remove, separated by commas, or type `c` now to cancel."
            prompt_msg = await view_preamble(ctx, lined_preamble, prompt)
            response = await ctx.input(prompt_msg=prompt_msg)
            if response is None:
                await ctx.reply("Query timed out, aborting.")
                return
            if response.lower == "c":
                await ctx.reply("User cancelled, aborting.")
                return
            nums = [num.strip() for num in response.split(',')]
            if not all(num.isdigit() for num in nums):
                await ctx.reply("Couldn't understand your selection, aborting.")
                return
            nums = [int(num) - 1 for num in nums]
            if not all(0 <= num < len(lines) for num in nums):
                await ctx.reply("This line doesn't exist! Aborting.")
                return

            to_remove = nums

        if to_remove:
            # Prompt the user to confirm they want to remove these lines
            for_removal = "\n".join([lines[i] for i in to_remove])
            prompt = "Please confirm removal of the following lines from your preamble."
            result = await confirm(ctx, prompt, for_removal)
            if result is None:
                await ctx.reply("Query timed out, aborting.")
                return
            if not result:
                await ctx.reply("User cancelled, aborting.")
                return

            new_preamble = "\n".join([line for i, line in enumerate(lines) if i not in to_remove])

        if new_preamble is not None:
            # Finally, update the preamble
            await ctx.data.users.set(ctx.authid, "previous_preamble", preamble)
            await ctx.data.users.set(ctx.authid, "latex_preamble", new_preamble)

            await ctx.reply("Your preamble has been updated!")
            await preamblelog(ctx, "Material was removed from the preamble", source=new_preamble)
            return

    # At this point, the user wants to view, replace, or add to their preamble.

    # Handle a request to replace the preamble
    if ctx.flags['replace']:
        if not new_source:
            # Prompt the user for the new preamble
            prompt = "Please enter your new preamble, or `c` to cancel.\
                \nIf you wish to upload a file as your preamble, cancel now and rerun this command with the file attached."
            new_source = await ctx.input(prompt, timeout=600)
            if not new_source:
                await ctx.reply("Query timed out, aborting.")
                return
            if new_source.lower() == 'c':
                await ctx.reply("User cancelled, aborting.")
                return

        new_submission = new_source

        # Confirm submission
        prompt = "Please confirm your submission of the following preamble."
        result = await confirm(ctx, prompt, new_submission)
        if result is None:
            await ctx.reply("Query timed out, aborting.")
            return
        if not result:
            await ctx.reply("User cancelled, aborting.")
            return

        await submit_preamble(ctx, ctx.author, new_submission, "User wishes to replace their preamble")
        await ctx.reply("Your preamble submission has been sent to my managers for review!\
                        \nIf you wish to retract your submission, please use `preamble --retract`.")
        return

    # Handle a request to add a new package to the preamble, possibly from the whitelist
    if ctx.flags['usepackage']:
        # Not yet implemented
        pass

    # Handle a request to add material to the preamble
    if ctx.flags['add'] or new_source:
        if not new_source:
            # Prompt the user for the material they want to add
            prompt = "Please enter the lines you wish to add to your preamble."
            new_source = await ctx.input(prompt, timeout=600)
            if not new_source:
                await ctx.reply("Query timed out, aborting.")
                return
            if new_source.lower() == 'c':
                await ctx.reply("User cancelled, aborting.")
                return

        new_submission = "{}\n{}".format(preamble, new_source)

        # Confirm submission
        prompt = "Please confirm your submission of the following preamble."
        result = await confirm(ctx, prompt, new_submission)
        if result is None:
            await ctx.reply("Query timed out, aborting.")
            return
        if not result:
            await ctx.reply("User cancelled, aborting.")
            return

        await submit_preamble(ctx, ctx.author, new_submission, "User wishes to add {} lines to their preamble".format(len(new_source)))
        await ctx.reply("Your preamble submission has been sent to my managers for review!\
                        \nIf you wish to retract your submission, please use `preamble --retract`.")
        return

    # If the user doesn't want to edit their preamble, they must just want to view it
    title = "Your current preamble. Use texconfig to see other LaTeX config options!"
    await view_preamble(ctx, preamble, title, header=header, file_react=True, file_message="Current Preamble")


async def load_channels(bot):
    bot.objects["latex_preamble_subch"] = discord.utils.get(bot.get_all_channels(), id=bot.bot_conf.get("preamble_ch"))
    bot.objects["latex_preamble_logch"] = discord.utils.get(bot.get_all_channels(), id=bot.bot_conf.get("preamble_logch"))


async def cache_pending_preambles(bot):
    bot.objects["pending_preambles"] = {}
    for userid in await bot.data.users.find_not_empty("pending_preamble"):
        info = await bot.data.users.get(userid, "pending_preamble_info")
        bot.objects["pending_preambles"][str(userid)] = info


def load_into(bot):
    bot.add_after_event("ready", load_channels, priority=10)
    bot.add_after_event("ready", cache_pending_preambles, priority=10)
    bot.data.users.ensure_exists("pending_preamble", "pending_preamble_info", "previous_preamble", "latex_preamble", shared=True)
