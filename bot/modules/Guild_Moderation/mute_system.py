import traceback
import logging
import asyncio
import datetime as dt

from registry import tableInterface, Column, ColumnType, ForeignKey, ReferenceAction, tableSchema

from .module import guild_moderation_module as module
from .mute_utils import mute_member, unmute_member, ActionState


# TODO: Remute on user join? Optionally?
class TimedMuteGroup:
    # Client, attached during initialisation
    _client = None  # type: cmdClient

    # Data interfaces, attached during initialisation
    _group_data = None
    _member_data = None

    # Guild TimedMuteGroup cache, keyed on `guildid` then `memberid`.
    _guild_caches = {}  # type: Dict[int, Dict[int, TimedMuteGroup]]

    # Global TimedMuteGroup cache, keyed on groupid
    _mutegroup_cache = {}  # type: Dict[int, TimedMuteGroup]

    def __init__(self,
                 guild, role,
                 groupid, memberids,
                 unmute_timestamp,
                 muted_timestamp=None, modid=0, duration=0, reason=None, reference=None):
        if groupid in self. _mutegroup_cache:
            raise ValueError("Duplicate groupid for TimedMute.")

        # Discord objects
        self.guild = guild
        self.role = role

        # Mute group
        self.groupid = groupid
        self.memberids = memberids
        self.unmute_timestamp = unmute_timestamp

        # Extra optional mute action data
        self.muted_timestamp = muted_timestamp
        self.modid = modid
        self.duration = duration
        self.reason = reason
        self.reference = reference

        # Task controlling the scheduled group unmute
        self._task = None

        # Whether the unmute is to be cancelled
        self._cancelled = False

    @property
    def guild_cache(self):
        """
        The timed mute user cache associated to the current guild.
        Creates the cache if it doesn't exist.
        """
        cache = self._guild_caches.get(self.guild.id, None)
        if cache is None:
            cache = self._guild_caches[self.guild.id] = {}
        return cache

    @classmethod
    async def new_timed_mute(cls, guild, role, groupid, duration, members, reason=None, modid=None, **kwargs):
        """
        Mute a new group of users for a specified duration.
        Creates the TimedMuteGroup, mutes the members, schedules the unmute, and posts to the modlog.
        Returns a list of (member, ActionState) tuples.
        """
        mute_reason = "Muted by {}".format(modid if modid is not None else "?")
        mute_reason += ": {}".format(reason) if reason else "."

        # Mute users
        results = await asyncio.gather(
            *(mute_member(guild, role, member, audit_reason=mute_reason) for member in members)
        )
        member_results = list(zip(members, results))

        if any(result == ActionState.SUCCESS for result in results):
            # Calculate unmute timestamp
            muted_at = dt.datetime.utcnow()
            unmute_at = muted_at + dt.timedelta(seconds=duration)

            # Post to modlog
            # TODO: Post in modlog
            # Set reference

            # Create mute group, save, and activate it
            tgroup = cls(
                guild, role,
                groupid, [member.id for member, result in member_results if result == ActionState.SUCCESS],
                int(unmute_at.timestamp()),
                muted_timestamp=int(muted_at.timestamp()),
                duration=duration,
                **kwargs
            )
            tgroup.write()
            tgroup.load()

        return member_results

    # Client initialisation and launch methods
    @classmethod
    def setup(cls, client):
        """
        Initialisation task.
        Attaches the client, along with the guild and member data interfaces.
        Also adds the mute cache as a client object for external use.
        """
        # Attach the client
        cls._client = client

        # Attach the data interfaces to the class
        cls._group_data = client.data.guild_timed_mute_groups
        cls._member_data = client.data.guild_timed_mutes_members

        # Attach the guild caches to the client
        client.objects['timed_unmutes'] = cls._mutegroup_cache

    @classmethod
    async def launch(cls, client):
        """
        Launch task.
        Populate the caches and schedule the pending mutes.
        """
        client.log(
            "Populating timed mute cache.",
            context="LAUNCH_TIMED_MUTES"
        )
        # Collect the group members
        group_members = {}  # groupid: list_of_members
        for row in cls._member_data.select_where():
            if row['groupid'] not in group_members:
                group_members[row['groupid']] = []
            group_members[row['groupid']].append(row['memberid'])

        # Construct the groups
        group_counter = 0
        cleanup = []  # List of groupids that are "stale" (e.g. non-existent guild or role), and should be removed
        for row in cls._group_data.select_where():
            _cleanup = False

            # Extract the guild
            guild = client.get_guild(row['guildid'])
            if guild is not None:
                # Extract the mute role
                role = guild.get_role(row['roleid'])
                if role is not None and row['groupid'] in group_members:
                    # Create the TimedMute, load it, and schedule it
                    cls(
                        guild,
                        role,
                        row['groupid'],
                        group_members[row['groupid']],
                        row['unmute_timestamp'],
                        row['muted_timestamp'],
                        row['modid'],
                        row['duration'],
                        row['reason'],
                        row['reference']
                    ).load()

                    group_counter += 1
                else:
                    # No muterole, or the group doesn't have any members
                    _cleanup = True
            else:
                # No guild
                _cleanup = True

            if _cleanup:
                cleanup.append(row['groupid'])

        # Log the loaded mute groups
        client.log(
            "Loaded and scheduled {} timed mute groups.".format(group_counter),
            context="LAUNCH_TIMED_MUTES"
        )

        # Handle cleanup if required
        if cleanup:
            client.log(
                "Cleaning up stale timed mutes.",
                context="LAUNCH_TIMED_MUTES"
            )
            cls._group_data.delete_where(groupid=cleanup)
            client.log(
                "Successfully cleaned up {} stale timed mute groups.".format(len(cleanup)),
                context="LAUNCH_TIMED_MUTES"
            )

    # Data interface methods
    def write(self):
        """
        Write this TimedMuteGroup to data, overwriting any existing groups with the same `groupid`.
        """
        # Delete existing group
        self._group_data.delete_where(groupid=self.groupid)

        # Save group information
        self._group_data.insert(
            groupid=self.groupid,
            guildid=self.guild.id,
            roleid=self.role.id,
            unmute_timestamp=self.unmute_timestamp,
            muted_timestamp=self.muted_timestamp,
            modid=self.modid,
            duration=self.duration,
            reason=self.reason,
            reference=self.reference
        )

        # Save member information
        self._member_data.insert_many(
            *[(self.groupid, memberid) for memberid in self.memberids],
            insert_keys=('groupid', 'memberid')
        )

        return self

    # Activation and deactivation of the TimedMuteGroup
    def load(self):
        """
        Adds the TimedMuteGroup to the relevant caches, and schedules the unmute.
        Removes members from any other groups.
        Returns `self` for easy chaining.
        """
        # Add mute group to the global cache
        self._mutegroup_cache[self.groupid] = self

        # Add users to the guild cache, and remove them from any existing mute groups
        for memberid in self.memberids:
            if memberid in self.guild_cache:
                self.guild_cache[memberid].remove(memberid)
            self.guild_cache[memberid] = self

        self._schedule()
        return self

    def unload(self):
        """
        Removes the TimedMuteGroup from the caches and cancels the unmute task.
        """
        self._cancel()

        # Remove the mute from cache, if it still exists
        for memberid in self.memberids:
            self.guild_cache.pop(memberid, None)
        self._mutegroup_cache.pop(self.groupid, None)

        # Remove the mute from data
        self._group_data.delete_where(groupid=self.groupid)

    # Application interface and member management
    def remove(self, *memberids):
        """
        Remove a sequence of users from the mute group.
        If there are no users left, unloads the group and cancels the unmute task.
        """
        # Remove from internal mute group list
        self.memberids = [memberid for memberid in self.memberids if memberid not in memberids]

        # Remove from guild cache
        [self.guild_cache.pop(memberid, None) for memberid in memberids]

        # Remove from data
        self._member_data.delete_where(groupid=self.groupid, memberid=memberids)

        # Close and cancel if there are no users left
        if not self.memberids:
            self.unload()

    # Internal creation and cancellation of the mute task
    def _schedule(self):
        """
        Schedule the TimedMute and create the unmute task.
        """
        # Create the group unmute task as self._task
        self._task = asyncio.create_task(self._unmute_wrapper())

    def _cancel(self):
        """
        Cancel the unmute task, if it is running.
        """
        self._cancelled = True
        if not self._cancelled and (self._task and not self._task.done):
            self._task.cancel()

    # Internal unmute system
    async def _unmute_wrapper(self):
        """
        Unmute wrapper which runs `apply_unmutes` at `self.unmute_timestamp`.
        """
        try:
            # Sleep for the required time
            await asyncio.sleep(self.unmute_timestamp - dt.datetime.utcnow().timestamp())

            # Execute the unmutes
            await self._unmute_members()
            await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            # Unknown exception!
            full_traceback = traceback.format_exc()

            self._client.log(
                ("Caught an unknown exception during schedule unmute with groupid {groupid}."
                 "{traceback}").format(
                     groupid=self.groupid,
                     traceback='\n'.join('\t' + line for line in full_traceback.splitlines()),
                 ),
                context="sid:{}".format(self.groupid),
                level=logging.ERROR)

            raise e

    async def _unmute_members(self):
        """
        Attempt to apply the unmutes.
        Posts to the modlog with a summary if possible.
        Closes the TimedUnmute if there are no users left in the group.
        """
        results = await asyncio.gather(
            *(unmute_member(self.guild,
                            self.role,
                            memberid,
                            audit_reason="Automatic timed unmute.") for memberid in self.memberids)
        )
        # TODO: Smart save/retry logic
        # TODO: Mute role persistence stuff
        # TODO: Post in modlog
        print(results)
        self.unload()


# Attach the initialisation tasks
module.init_task(TimedMuteGroup.setup)
module.launch_task(TimedMuteGroup.launch)


# Define data schemas
group_schema = tableSchema(
    "guild_timed_mute_groups",
    Column('app', ColumnType.SHORTSTRING, primary=True, required=True),
    Column('groupid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('guildid', ColumnType.SNOWFLAKE, required=True),
    Column('roleid', ColumnType.SNOWFLAKE, required=True),
    Column('unmute_timestamp', ColumnType.INT, required=True),
    Column('muted_timestamp', ColumnType.INT, required=False),
    Column('modid', ColumnType.SNOWFLAKE, required=True),
    Column('duration', ColumnType.INT, required=True),
    Column('reason', ColumnType.MSGSTRING, required=False),
    Column('reference', ColumnType.MSGSTRING, required=False),
)

member_schema = tableSchema(
    "guild_timed_mute_members",
    Column('app', ColumnType.SHORTSTRING, primary=True, required=True),
    Column('groupid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('memberid', ColumnType.SNOWFLAKE, primary=True, required=True),
    ForeignKey("app, groupid", group_schema.name, "app, groupid", on_delete=ReferenceAction.CASCADE)
)


# Attach data interfaces
@module.data_init_task
def attach_timed_mute_data(client):
    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, group_schema, shared=False),
        "guild_timed_mute_groups"
    )

    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, member_schema, shared=False),
        "guild_timed_mutes_members"
    )
