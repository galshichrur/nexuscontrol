from db.components import Field
from db.table import Table

# Connections table
agent_id = Field("agent_id", str, primary=True, unique=True)  # Agent unique UUID4
connection_time = Field("connection_time", str)  # A timestamp of when the agent connected.
disconnect_time = Field("disconnect_time", str)  # A timestamp of when the agent disconnected.
status = Field("status", bool)

hostname = Field("hostname", str)
ip_address = Field("ip_address", str)
port = Field("port", str)

agents_table = Table("agents", (agent_id, connection_time, disconnect_time, status, hostname, ip_address, port))
