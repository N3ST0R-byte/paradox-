from logger import log
from .module import meta_module as module

"""
Provides a prefix command.

Commands provided:
    prefix:
        View current valid bot prefixes and set a personal prefix.

Initialisation:
    load_user_prefixes:
        Read user prefixes from data and load them into the cache.
    ensure_prefix_properties:
        Ensure that the required user and guild properties exist.

Client objects:
    user_prefix_cache:  Dict[int, str]
        Dictionary `{userid: prefix}` of custom user prefixes.

User properties:
    custom_prefix: str
        (app agnostic, user configured)
        Current user custom prefix.
        Must be less than `5` characters.

Guild properties:
    guild_prefix: str
        (app agnostic, admin configured)
        Current guild custom prefix.
"""


@module.cmd("prefix",
            desc="View bot prefixes and set a personal prefix.",
            aliases=["myprefix"],
            flags=["set"])
async def cmd_prefix(ctx, flags):
    """
    Usage``:
        {prefix}prefix [--set <custom prefix>]
    Description:
        Displays the current command prefixes available for the bot,
        including the global, guild, and personal prefix where applicable.

        Use `{prefix}config prefix <prefix>` to change the guild prefix.
        *Note that mentioning the bot will always work as a prefix.*
    Flags::
        set:: Set your personal prefix (this will work additionally to the current prefixes).
    Related:
        config
    Examples``:
        {prefix}prefix
        {prefix}prefix --set !!
    """
    if flags["set"]:
        # First check if the provided prefix it is below the maximum length
        if len(ctx.args) > 5:
            return await ctx.error_reply("Sorry, the maximum length of a personal prefix is `5` characters.")

        # Set the prefix user property
        ctx.client.data.users.set(ctx.author.id, "custom_prefix", ctx.args)

        # Update the user prefix cache
        ctx.client.objects["user_prefix_cache"][ctx.author.id] = ctx.args

        # Inform the user
        await ctx.reply("Your personal command prefix has been set to `{}`. "
                        "Mentions and the current guild or global prefix will still function.".format(ctx.args))
    else:
        # Retrieve the current bot prefixes and build the response lines
        # User's personal prefix
        personal_prefix = ctx.client.data.users.get(ctx.author.id, "custom_prefix")
        if personal_prefix:
            personal_str = "Your personal prefix is `{}`.\n".format(personal_prefix)
        else:
            personal_str = "You have not set a personal prefix.\n"

        # Guild prefix, if applicable
        guild_str = ""
        guild_prefix = None
        if ctx.guild:
            guild_prefix = ctx.client.data.guilds.get(ctx.guild.id, "guild_prefix")
            guild_str = ("The guild prefix  is `{}`.\n".format(guild_prefix)
                         if guild_prefix else "No custom guild prefix set.\n")

        # Global prefix
        global_str = "The default prefix is `{}`{}.".format(
            ctx.client.prefix,
            " (not active in favour of the guild prefix)" if guild_prefix else ""
        )

        # Create the response and reply
        await ctx.reply(
            "{}{}{}\nMentioning me will always work as a prefix:{}".format(
                personal_str, guild_str, global_str, ctx.client.user.mention
            )
        )


@module.launch_task
async def ensure_prefix_properties(client):
    client.data.users.ensure_exists("custom_prefix", shared=False)
    client.data.guilds.ensure_exists("guild_prefix", shared=False)


@module.launch_task
async def load_user_prefixes(client):
    """
    Retrieve the user prefixes from the database and fill the cache
    """
    user_prefix_cache = {}
    for row in client.data.users.get_all_with("custom_prefix"):
        user_prefix_cache[int(row['userid'])] = row['value']

    client.objects["user_prefix_cache"] = user_prefix_cache

    log("Loaded {} custom user prefixes.".format(len(user_prefix_cache)),
        context="LOAD_USER_PREFIXES")
