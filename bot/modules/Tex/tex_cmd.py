from .module import latex_module as module

from .core.LatexContext import LatexContext
from .core.LatexGuild import LatexGuild
from .core.LatexUser import LatexUser
from .core.tex_utils import ParseMode


@module.cmd("tex",
            desc="Render LaTeX code.",
            aliases=[',', 'mtex', 'align', 'latex', 'texsp', 'texw'],
            flags=['config', 'keepsourcefor', 'color', 'colour', 'alwaysmath', 'allowother', 'name'])
async def cmd_tex(ctx, flags):
    """
    Usage``:
        {prefix}tex <code>
        {prefix}, <code>
        {prefix}mtex <equations>
        {prefix}align <align block>
        {prefix}texsp <code>
    Description:
        Compiles and displays [LaTeX]() document code.
        For a quick introduction to using LaTeX, see our [cheatsheet]().

        The output is extensively configurable, see `{prefix}help texconfig`
        for more information about the possible configuration options.

        LaTeX macros and packages may also be used in this command via
        inclusion into the *preamble*, see `{prefix}help preamble` for more information.

        If a guild or user has *latex recognition* enabled (see `{prefix}config latex` and `{prefix}help autotex`),
        messages containing LaTeX will automatically be compiled and this command
        is generally not required.
    Aliases::
        tex: The default mode, compile the code as written inside a LaTeX `document` environment.
        , / mtex: Render the code in maths mode. Specifically, in a `gather*` environment.
        align: Render the code in an align block. Specifically, in an `align*` environment.
        texsp: Same as `tex`, but ||spoiler|| the output image.
        texw: Don't crop the output after compilation.
    Related:
        autotex, texconfig, preamble
    Examples``:
        {prefix}tex This is a fraction: \\(\\frac{{1}}{{2}}\\)
        {prefix}, \\int^\\infty_0 f(x)~dx
        {prefix}align a + 1 &= 2\\\\ a &= 1
    """
    # Handle flags
    if any(flags.values()):
        return await ctx.error_reply(
            "LaTeX configuration has moved to the `texconfig` command.\n"
            "Please see `{}help texconfig` for usage."
        ).format(ctx.best_prefix)

    # Handle empty input
    if not ctx.args:
        return await ctx.error_reply(
            "Please give me something to compile, for example "
            "```tex\n"
            "{0}tex The solutions to \\(x^2 = 1\\) are \\(x = \\pm 1\\)."
            "```"
            "See `{0}help` and `{0}help tex` for detailed usage and further examples!".format(ctx.best_prefix())
        )

    # Handle `tex help`
    if ctx.args.lower() == 'help':
        return await ctx.error_reply("Please use `{}help tex` for command help.")

    # Get latex user and guild
    lguild = LatexGuild.get(ctx.guild.id if ctx.guild else 0)
    luser = LatexUser.get(ctx.author.id)

    # Determine parse mode and flags
    flags = {}
    parse_mode = ParseMode.DOCUMENT

    lalias = ctx.alias.lower()
    if lalias in [',', 'mtex']:
        parse_mode = ParseMode.GATHER
    elif lalias == 'align':
        parse_mode = ParseMode.ALIGN
    elif lalias == 'texsp':
        flags["spoiler"] = True
    elif lalias == "texw":
        flags["wide"] = True

    # Clean mentions
    content = ctx.clean_arg_str()

    # Parse source
    source = LatexContext.parse_content(content, parse_mode, **flags)

    # Create the LatexContext
    lctx = LatexContext(ctx, source, lguild, luser)

    # Make the LaTeX
    await lctx.make()

    # Keep the command alive until the latex context dies
    await lctx.lifetime()
