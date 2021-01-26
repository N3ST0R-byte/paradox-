"""
ABC and data definitions for manual moderation tickets.
"""
import discord

from registry import tableInterface, Column, ColumnType, tableSchema, ForeignKey, ReferenceAction

from .module import guild_moderation_module as module


class ModActionTicket:
    __slots__ = (
        'guildid',
        'modid',
        'memberids',
        'ticketid',
        'app',
        'msgid',
        'auditid',
        'reason',
        'created_at',
        '_guild_ticketid',
    )
    _client = None
    _ticket_data = None
    _ticketview_data = None
    _member_data = None

    def __init__(self, guildid, modid, memberids, *args,
                 ticketid=None, app=None, msgid=None, auditid=None, reason=None, created_at=None, **kwargs):
        self._guild_ticketid = None

        self.guildid = guildid
        self.modid = modid
        self.memberids = memberids

        self.ticketid = ticketid
        self.app = app if app is not None else self._client.app
        self.msgid = msgid
        self.auditid = auditid
        self.reason = reason
        self.created_at = created_at

    @property
    def embed(self):
        """
        Returns the ticket embed to be posted in the modlog.
        """
        raise NotImplementedError

    @property
    def guild_ticketid(self):
        """
        Guild-local id of this ticket.
        """
        # Get the guild ticketid if it hasn't already been retrieved
        if self._guild_ticketid is None:
            if self.ticketid is None:
                raise ValueError("Attempting to get guild ticketid of ticket without a global ticketid!")
            else:
                row = self._ticketview_data.select_one_where(ticketid=self.ticketid)
                if row is None:
                    raise ValueError("Ticket global ticketid does not exist!")
                else:
                    self._guild_ticketid = row['guild_ticketid']

        return self._guild_ticketid

    @classmethod
    def setup(cls, client):
        cls._client = client
        cls._ticket_data = client.data.guild_mod_tickets
        cls._member_data = client.data.guild_mod_ticket_members
        cls._ticketview_data = client.data.guild_mod_tickets_view

    @classmethod
    async def create_ticket(cls, guildid, modid, memberids, *args, post=True, **kwargs):
        """
        Creates a new ticket, saves it, and posts it in the modlog (if possible).
        Returns the created ticket.
        """
        # Create the ticket
        ticket = cls(guildid, modid, memberids, *args, **kwargs)

        # Save the ticket data
        curs = cls._ticket_data.insert(
            app=cls._client.app,
            guildid=guildid,
            modid=modid,
            msgid=ticket.msgid,
            auditid=ticket.auditid,
            reason=ticket.reason,
        )

        # Retrieve the ticket id
        ticket.ticketid = curs.lastrowid

        # Save the member data
        cls._member_data.insert_many(
            *((ticket.ticketid, memberid) for memberid in memberids),
            insert_keys=('ticketid', 'memberid')
        )

        # Post the ticket to the modlog, if required and possible
        if post:
            await ticket.post()

        return ticket

    @classmethod
    def ticket_from_data(cls, data_row, memberids):
        """
        Instantiate a ticket from a data row.
        Intended to be overridden if the ticket view data interface is overridden.
        """
        return cls(
            guildid=data_row['guildid'],
            modid=data_row['modid'],
            memberids=memberids,
            msgid=data_row['msgid'],
            auditid=data_row['auditid'],
            reason=data_row['reason'],
            created_at=data_row['created_at'],
            app=data_row['app'],
            ticketid=data_row['ticketid']
        )

    @classmethod
    def fetch_tickets_where(cls, **kwargs):
        """
        Fetch tickets matching the given criteria
        """
        tickets = []
        member_rows = []

        memberid = kwargs.pop('memberid', None)
        if memberid is not None:
            rows = cls._member_data.select_where(memberid=memberid)
            ticketids = [row['ticketid'] for row in rows]

            given_ticketid = kwargs.pop('ticketid', None)
            if given_ticketid is None:
                kwargs['ticketid'] = ticketids
            elif isinstance(given_ticketid, (list, tuple)):
                kwargs['ticketid'] = [*given_ticketid, *ticketids]
            else:
                kwargs['ticketid'] = [given_ticketid, *ticketids]

        ticket_rows = cls._ticketview_data.select_where(**kwargs)
        if ticket_rows:
            ticketids = [row['ticketid'] for row in ticket_rows]
            member_rows = cls._member_data.select_where(ticketid=ticketids)

            ticket_members = {ticketid: [] for ticketid in ticketids}
            for row in member_rows:
                ticket_members[row['ticketid']].append(row['memberid'])

            for row in ticket_rows:
                tickets.append(
                    cls.ticket_from_data(row, memberids=ticket_members[row['ticketid']])
                )

        return tickets

    def update(self, **kwargs):
        """
        Updates the ticket information with the provided arguments, and saves the ticket to data.
        Returns the updated ticket.
        """
        for attr, value in kwargs.items():
            setattr(self, attr, value)

        new_members = kwargs.pop('members', None)

        if kwargs:
            self._ticket_data.update_where(
                kwargs,
                ticketid=self.ticketid
            )

        if new_members is not None:
            self._member_data.delete_where(ticketid=self.ticketid)
            self._member_data.insertmany(
                ('ticketid', 'memberid'),
                *((self.ticketid, memberid) for memberid in new_members)
            )

    async def post(self):
        """
        Updates the ticket embed in the modlog.
        If it doesn't exist or cannot be found, posts a new ticket and saves it.
        If a new ticket is posted, updates self with the modlog message id.
        Fails silently with most error conditions (e.g. guild or modlog not found).
        """
        # Get the modlog
        modlog = self._client.guild_config.modlog.get(self._client, self.guildid).value

        if modlog is not None:
            message = None
            if self.msgid:
                # Get the message, if possible
                try:
                    message = await modlog.fetch_message(self.msgid)
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    return None
                except discord.HTTPException:
                    return None

            if message is not None:
                # Edit the message
                await message.edit(embed=self.embed)
            else:
                # Post the message
                message = await modlog.send(embed=self.embed)

                # Save the message id
                self.update(msgid=message.id)


module.init_task(ModActionTicket.setup)


# Define data schemas
ticket_schema = tableSchema(
    "guild_moderation_tickets",
    Column('ticketid', ColumnType.INT, autoincrement=True, primary=True),
    Column('app', ColumnType.SHORTSTRING, required=True),
    Column('guildid', ColumnType.SNOWFLAKE, required=True),
    Column('modid', ColumnType.SNOWFLAKE, required=True),
    Column('msgid', ColumnType.SNOWFLAKE, required=False),
    Column('auditid', ColumnType.SNOWFLAKE, required=False),
    Column('reason', ColumnType.MSGSTRING, required=False),
    Column('created_at', ColumnType.TIMESTAMP, required=True, default="CURRENT_TIMESTAMP"),
)

member_schema = tableSchema(
    "guild_moderation_ticket_members",
    Column('ticketid', ColumnType.INT, required=True),
    Column('memberid', ColumnType.SNOWFLAKE, required=True),
    ForeignKey('ticketid', ticket_schema.name, 'ticketid', on_delete=ReferenceAction.CASCADE)
)

ticketview_raw_schema = """\
CREATE VIEW
    guild_moderation_tickets_gtid
AS
SELECT
    *,
    row_number() OVER (PARTITION BY guildid ORDER BY ticketid) AS guild_ticketid
FROM
    guild_moderation_tickets;
"""


# Attach data interfaces
@module.data_init_task
def attach_mod_ticket_data(client):
    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, ticket_schema, shared=True),
        "guild_mod_tickets"
    )

    client.data.attach_interface(
        tableInterface(
            client.data,
            "guild_moderation_tickets_gtid",
            client.app,
            ticket_schema.interface_columns + (("guild_ticketid", int),),
            mysql_schema=ticketview_raw_schema,
            sqlite_schema=ticketview_raw_schema
        ),
        "guild_mod_tickets_view"
    )

    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, member_schema, shared=True),
        "guild_mod_ticket_members"
    )
    pass
