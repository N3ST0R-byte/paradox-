from paraModule import paraModule
from registry import propInterface


# Property table information
prop_table_info = [
        ("users", "users", ["userid"]),
        ("guilds", "guilds", ["guildid"]),
        ("members", "members", ["guildid", "userid"])
]

propertyModule = paraModule(
    "property_tables",
    description="Skeleton module which loads the core property tables."
)


@propertyModule.data_init_task
def load_property_tables(client):
    # Get the current app name
    app = client.conf.get("APP", "")

    # If the app is default the db app is empty
    if app == "default":
        app = ""

    # Get the data connector
    conn = client.data

    for attr, table, keys in prop_table_info:
        interface = propInterface(conn, table, keys, app)
        conn.attach_interface(interface, attr)
