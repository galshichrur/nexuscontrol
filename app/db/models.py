from db.components import Field
from db.table import Table

# Connections table

# Fields set by server.
agent_id = Field("agent_id", str, primary=True, unique=True)  # Agent unique UUID4
name = Field("name", str)
connection_time = Field("connection_time", str)  # A timestamp of when the agent connected.
latest_ping_time = Field("latest_ping_time", str)
port = Field("port", str)

# Data passed by agent upon the first connection.
hostname = Field("hostname", str)
cwd = Field("cwd", str)
os_name = Field("os_name", str)
os_version = Field("os_version", str)
os_architecture = Field("os_architecture", str)
local_ip = Field("local_ip", str)
public_ip = Field("public_ip", str)
mac_address = Field("mac_address", str)
is_admin = Field("is_admin", bool)
username = Field("username", str)

agents_table = Table("agents", (agent_id, name, connection_time, latest_ping_time, port, hostname, cwd, os_name, os_version, os_architecture, local_ip, public_ip, mac_address, is_admin, username))
