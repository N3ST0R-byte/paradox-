import discord

from utils.lib import prop_tabulate
from utils.ctx_addons import best_prefix  # noqa

from settings import BadUserInput

from wards import guild_manager

from .module import guild_admin_module as module


conf_pages = {
    "General options": ["Guild admin", "Starboard", "Mathematical"],
    "Manual Moderation settings": ["Moderation", "Logging"],
    "Greeting and Farewell messages": ["Greeting message", "Farewell message"]
}

# TODO: Cat descriptions
# TODO: Read wards
# TODO: Write wards


async def _build_config_pages(ctx, show_help=True):
    """
    Build guild configuration pages.
    """
    cats = {}
    pages = []

    # Generated sorted lists of options in each cat
    for option in sorted(ctx.client.guild_config.settings.values(), key=lambda s: s.name):
        cat = option.category
        if cat not in cats:
            cats[cat] = []
        cats[cat].append(option)

    # Generate embed pages
    for page_title, page_cats in conf_pages.items():
        # Initialise the embed
        page_embed = discord.Embed(title=page_title, color=discord.Colour.teal())

        # Build one cat at a time
        for cat in page_cats:
            if cat in cats:
                # Tabulate option name and values
                names = []
                values = []
                for option in cats[cat]:
                    names.append(option.name)
                    if show_help:
                        values.append(option.desc)
                    elif await option.read_check.run(ctx):
                        values.append(option.get(ctx.client, ctx.guild.id).formatted or "Not Set")
                    else:
                        values.append("Hidden")
                cat_str = prop_tabulate(names, values)

                # Add table as the cat field
                page_embed.add_field(name=cat, value=cat_str, inline=False)

        # Finalise the embed
        page_embed.set_footer(
            text="Use {0}config <option> and {0}config <option> <value> to see or set an option.".format(
                ctx.best_prefix()
            )
        )
        # Add the page embed
        pages.append(page_embed)

    # Return the list of pages
    return pages


@module.cmd("config",
            desc="View and set the guild configuration.")
async def cmd_config(ctx):
    """
    Usage``:
        {prefix}config
        {prefix}config help
        {prefix}config <option>
        {prefix}config <option> <value>
    Description:
        Display the current guild configuration, show option information, or set an option.

        Use `{prefix}config help` to display short summaries of each option,
        and use `{prefix}config <option>` to display detailed information about a particular option.

        Use `{prefix}config <option> <value>` to set an option.
        Note that most options require moderator or administrator permissions to set.
    Examples``:
        {prefix}config prefix
        {prefix}config prefix {prefix}
    """
    # Prebuild dictionary of setting names
    settings = {setting.name: setting for setting in ctx.client.guild_config.settings.values()}

    params = ctx.args.split(maxsplit=1)
    if not ctx.args:
        # Handle empty argument case, show options with values
        pages = await _build_config_pages(ctx, show_help=False)
        await ctx.pager(pages)
    elif ctx.args.lower() == "help":
        # Handle sole help argument, show options with descriptions
        pages = await _build_config_pages(ctx, show_help=True)
        await ctx.pager(pages)
    elif params[0] not in settings:
        # Handle unrecognised option
        await ctx.error_reply("Unrecognised guild option `{}`. Use `{}config help` to see all the options.".format(
            params[0],
            ctx.best_prefix()
        ))
    elif len(params) == 1:
        # Assume argument is an option, display option information
        await ctx.reply(embed=settings[params[0]].get(ctx.client, ctx.guild.id).embed)
    else:
        # Handle setting an option
        option, value = params
        setting = settings[option]

        # Check write permissions
        write_ward = setting.write_check or guild_manager
        if not await write_ward.run(ctx):
            await ctx.error_reply(write_ward.msg)
        else:
            # Set the option
            try:
                (await setting.parse(ctx, value)).write()
            except BadUserInput as e:
                if e.msg:
                    await ctx.error_reply(e.msg)
                else:
                    await ctx.error_reply(
                        "Did not understand the provided value, "
                        "please check the accepted values and try again."
                    )
            else:
                await ctx.reply("The setting has been set successfully!")
