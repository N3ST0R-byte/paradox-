from . import Ticket, describes_ticket, TicketType


@describes_ticket(TicketType.UNMUTE)
class UnmuteTicket(Ticket):
    @property
    def embed(self):
        embed = super().embed
        embed.set_author(name="Unmute")
        return embed
