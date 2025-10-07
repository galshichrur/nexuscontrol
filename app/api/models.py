from pydantic import BaseModel


class ServerStatus(BaseModel):
    is_running: bool
    port: int
    host: str

class ServerStats(BaseModel):
    hostname: str
    local_ip: str
    public_ip: str
    mac_address: str
    cpu_usage: float
    memory_usage: float
    network_download_kbps: float
    network_upload_kbps: float
    os_name: str
    os_version: str
    os_architecture: str
    server_time: str
    server_start_time: str

class AgentData(BaseModel):
    agent_id: str
    name: str
    connection_time: str
    host: str
    port: str
    status: bool
    hostname: str
    cwd: str
    os_name: str
    os_version: str
    os_architecture: str
    local_ip: str
    public_ip: str
    mac_address: str
    is_admin: bool
    username: str

class AgentResponse(BaseModel):
    status: bool
    command_response: str | None = None
    cwd: str | None = None