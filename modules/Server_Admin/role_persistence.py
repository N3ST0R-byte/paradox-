import discord

"""
Handlers for role persistence, saving user roles upon leaving, and restoring on rejoin.

Handlers:
    store_roles:
        Triggers on member leaving
        Stores roles into a list of persistent roles
    recall_roles:
        Triggers on member joining
        Restores member's stored roles if possible

Member data:
    persistent_roles: int[]
        (app independent, automatic)
        Roles the member had when they last left the server.

Server data:
    role_persistence: bool
        (app independent, admin configured)
        Whether stored roles should be restored on member join.
"""


async def recall_roles(bot, member):
    # Quit if server doesn't have persistence enabled
    persist = await bot.data.servers.get(member.server.id, "role_persistence")
    if persist is not None and not persist:
        return

    # Quit if member has no stored roles
    stored = await bot.data.members_long.get(member.server.id, member.id, "persistent_roles")
    if stored is None or not stored:
        return

    # Build a list of roles which we have permission to add
    manager_roles = [r.position for r in member.server.me.roles if r.permissions.manage_roles or r.permissions.administrator]
    my_top_managerrole = max(manager_roles)
    roles_to_add = []

    for role in stored:
        actual_role = discord.utils.get(member.server.roles, id=role)
        if actual_role and actual_role.position < my_top_managerrole:
            roles_to_add.append(actual_role)

    # Give the member their roles, in theory
    try:
        await bot.add_roles(member, *roles_to_add)
    except discord.Forbidden:
        pass


async def store_roles(bot, member):
    role_list = [role.id for role in member.roles]
    await bot.data.members_long.set(member.server.id, member.id, "persistent_roles", role_list)


def load_into(bot):
    bot.data.servers.ensure_exists("role_persistence")
    bot.data.members_long.ensure_exists("persistent_roles")

    bot.add_after_event("member_join", recall_roles)
    bot.add_after_event("member_remove", store_roles)
