# TODO: Remute on user join? Optionally?
class TimedMute:
    """
    Class representing a simultaneous temporary mute with a fixed duration
    of (potentially) a number of members.

    client: cmdClient
        Client to use for muting and unmuting.
    guild: discord.Guild
        The guild to work in.
    role: discord.Role
        The mute role.
    sourceid: int
        A unique integer (generally a snowflake) labelling the `TimedMute`.
        The exact nature isn't important as long as it is unique.
        Typically the `id` of the original mute command.
    userids: List[int]
        A collection of userids affected by this timed mute.
        They do not need to be members of the guild.
    modid: int
        The id of the moderator who originally muted the users.
    end_timestamp: int
        The utc timestamp when the group should be unmuted.
    duration: int
        The duration of the mute.
    """

    def __init__(self, client, guild, role, sourceid, userids, modid, end_timestamp, duration):
        self.client = client
        self._data = client.data.guild_timed_mutes

        self.guild = guild
        self.role = role

        self.sourceid = sourceid
        self.userids = userids
        self.modid = modid
        self.duration = duration

        self._task = None

        # Slip into the cache on first creation
        self._guild_cache = self.get_guild_cache()
        for userid in userids:
            self._guild_cache[userid] = self

    def get_guild_cache(self):
        """
        Retrieve the guild cache timed mutes.
        Creates it if it doesn't exist.
        """
        if self.guild.id not in self.client.objects['timed_unmutes']:
            self.client.objects['timed_unmutes'][self.guild.id] = {}

        return self.client.objects['timed_unmutes'][self.guild.id]

    async def apply_mutes(self):
        """
        Attempt to apply the muted role to the users.
        Returns: (muted, failed)
            muted: The list of userids successfully muted.
            failed: The list of userids that couldn't be muted.
        """


    def schedule_unmute(self):
        # Create the group unmute task as self._task
        pass

    async def _mute(self, userid):
        """
        Attempt to apply a mute to a single user.
        """
        member = self.guild.get_member(userid)
        if not member:
            try:
                member = await self.guild.fetch_member(userid)
            except discord.HTTPException:
                return False
        if not member:
            return False
        try:
            await member.add_roles(self.role, reason="Muted by {}.".format(self.modid))
        except discord.Forbidden:
            return False
        except discord.HTTPException:
            return False
        else:
            return True

    async def _unmute(self):
        """
        Attempt to unmute a single user.
        """
        member = self.guild.get_member(userid)
        if not member:
            try:
                member = await self.guild.fetch_member(userid)
            except discord.HTTPException:
                return False
        if not member:
            return False
        try:
            await member.remove_roles(self.role, reason="Scheduled unmute.")
        except discord.Forbidden:
            return False
        except discord.HTTPException:
            return False
        else:
            return True
        pass

    def cancel_for(self, userid):
        """
        Remove a single userid from the group mute.
        """
        self.userids.remove(userid)
        if not self.userids:
            self.close()

    def close(self):
        """
        Handle final cleanup.
        """
        # Cancel unmute task if it still exists
        if self._task and not self._task.done():
            self._task.cancel()

        # Remove the mute from cache, if it still exists (which it shouldn't)
        for userid in self.userids:
            self._guild_cache.pop(userid, None)

        # Remove the mute from data
        self._data.delete_where(sourceid=self.sourceid)
