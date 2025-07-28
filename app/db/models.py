from components import Field
from table import Table

# Agent table
id_field = Field("id", int, primary=True)
hostname = Field("hostname", str, unique=True)
ip = Field("ip", str, unique=True)

agents_table = Table("agents", (id_field, hostname, ip))
