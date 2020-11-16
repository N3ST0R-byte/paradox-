from datetime import datetime

import discord

from utils.lib import prop_tabulate

from .module import latex_module as module

from .core.LatexUser import LatexUser
from .core.LatexGuild import LatexGuild


@module.cmd("texconfig",
            desc="View or modify your personal LaTeX rendering options.",
            aliases=['texflags'])
async def cmd_texconfig(ctx):
    """
    Usage``:
        {prefix}texconfig
        {prefix}texconfig help
        {prefix}texconfig <setting>
        {prefix}texconfig <setting> <value>
    Description:
        Configuration interface to view and modify the various
        options affecting your LaTeX compilation.
        These are *personal* configuration options,
        use the `config` command to view the *guild* configuration.

        When used with no arguments, displays your current configuration.

        When used with `help`, displays brief descriptions of each option.

        When used with a `setting`, displays detailed information
        about that setting, or sets the setting to the provided `value`.
    Related:
        autotex, preamble, tex
    Setting Examples``:
        {prefix}texconfig colour dark
        {prefix}texconfig keepsourcefor 30
        {prefix}texconfig colour dark
        {prefix}texconfig alwaysmath on
        {prefix}texconfig alwayswide on
        {prefix}texconfig namestyle NICKNAME
        {prefix}texconfig autotex_level STRICT
    """
    # Build the latex user
    luser = LatexUser.get(ctx.author.id)

    if not ctx.args or ctx.args.lower() == "help":
        # Display the configuration options with either values or the descriptions

        # Determine whether we want to show values or descriptions
        show_desc = bool(ctx.args)

        # Build the appropriate table
        properties = list(luser.settings.keys())
        if show_desc:
            values = [luser.settings[name].desc for name in properties]
        else:
            values = [
                luser.settings[name]._format_data(
                    ctx.client,
                    ctx.author.id,
                    luser.settings[name]._data_from_value(
                        ctx.client,
                        ctx.author.id,
                        getattr(luser, name)
                    )
                ) for name in properties
            ]
        setting_table = prop_tabulate(properties, values)

        # Create the description
        desc = (
            "{0}\n"
            "*To see more detailed information use `{1}texconfig <option>`.*\n"
            "*To set an option use `{1}texconfig <option> <value>`.*"
        ).format(setting_table, ctx.best_prefix())

        # Create the preamble field contents
        if show_desc:
            preamble_field = (
                "Personal persistent compilation preamble, "
                "used for defining macros and importing packages "
                "that may be used across all compilations.\n"
                "See `{}help preamble` for more information."
            ).format(ctx.best_prefix())
        else:
            if luser.preamble:
                preamble_field = (
                    "Using a custom personal preamble with `{}` lines!"
                ).format(len(luser.preamble))
            else:
                lguild = LatexGuild.get(ctx.guild.id if ctx.guild else 0)
                if lguild.preamble:
                    preamble_field = (
                        "No personal preamble, using the custom guild preamble with `{}` lines."
                    ).format(len(lguild.preamble))
                else:
                    preamble_field = (
                        "No personal or guild preamble, using the global default preamble."
                    )

            preamble_field += "\nUse `{}preamble` to view or modify your preamble!".format(ctx.best_prefix())

        # We have all the components, build the embed and post
        embed = discord.Embed(
            title="Personal LaTeX configuration.",
            description=desc,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Preamble", value=preamble_field)

        await ctx.reply(embed=embed)
    else:
        # View or set a given option

        # First obtain the option
        splits = ctx.args.split(maxsplit=1)
        option = splits[0].lower()
        valuestr = splits[1] if len(splits) > 1 else None

        # Handle aliases
        if option == "color":
            option = "colour"

        # Retrieve the corresponding setting, if possible
        if option == "preamble":
            return await ctx.error_reply("Use the `preamble` command to view or modify your preamble.")
        elif option not in luser.settings:
            return await ctx.error_reply(
                "I don't recognise the option `{}`. "
                "Use `{}texconfig` to see the list of options.".format(
                    option,
                    ctx.best_prefix()
                )
            )
        else:
            setting = luser.settings[option]
            current_value = getattr(luser, option)

        if not valuestr:
            # View information about the option
            await ctx.reply(embed=setting.info_embed(ctx, current_value))
        else:
            # Set the option
            await setting.user_set(ctx, valuestr)
