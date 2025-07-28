from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from db.engine import Engine
from db.models import agents_table, agent_id as agent_id_field
from db.query import Create, Select, Update
from server import Server
from config import Config
from pydantic import BaseModel


engine: Engine | None = None
server: Server | None = None


# Pydantic models
class ServerStatus(BaseModel):

    is_running: bool
    port: int
    host: str

class ServerControl(BaseModel):

    action: str

class AgentData(BaseModel):

    agent_id: str
    connection_time: str
    status: bool
    port: str
    hostname: str
    cwd: str
    os_name: str
    local_ip: str
    public_ip: str
    mac_address: str
    is_admin: bool
    username: str

class TerminalCommand(BaseModel):

    command: str
    agent_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):

    global server, engine

    # Init DB
    engine = Engine()
    init_db()

    # Start server
    server = Server(Engine)
    server.start(Config.HOST, Config.PORT)

    yield

    # Stop server
    server.stop()

    # Close DB
    engine.commit()
    engine.close()
    print("Server successfully stopped.")

def init_db() -> None:
    global engine
    engine.open(Config.DB_PATH)
    create = Create(agents_table, exists_ok=True)
    engine.execute(create)
    engine.commit()

    print("Database initialized.")
app = FastAPI(
    title=Config.API_TITLE, 
    version=Config.API_VERSION, 
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/server/status", response_model=ServerStatus)
async def get_server_status():

    return ServerStatus(
        is_running=server.is_running,
        port=server.port,
        host=server.host,
    )

@app.post("/server/control")
async def control_server(control: ServerControl):

    if control.action == "start":
        server.start(Config.HOST, Config.PORT)
        return {"message": "Server started successfully", "action": "start"}
    elif control.action == "stop":
        server.stop()
        return {"message": "Server stopped successfully", "action": "stop"}
    elif control.action == "restart":
        server.stop()
        server.start(Config.HOST, Config.PORT)
        return {"message": "Server restarted successfully", "action": "restart"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@app.get("/agents", response_model=List[AgentData])
async def get_agents() -> List[AgentData]:

    select_query = Select(agents_table).all()
    result = engine.execute(select_query)

    agents_list = [AgentData.model_validate(row) for row in result]
    return agents_list


@app.get("/agents/{agent_id}", response_model=AgentData)
async def get_agent(agent_id: str) -> AgentData:

    select_query = Select(agents_table).all()
    result = engine.execute(select_query)

    for row in result:
        agent = AgentData.model_validate(row)
        if agent.agent_id == agent_id:
            return agent

    raise HTTPException(status_code=404, detail="Agent not found")

@app.post("/agents/{agent_id}")
async def update_agent_name(agent_id: str, name: str) -> None:

    update = Update(agents_table).set({"hostname": name}).where(agent_id_field == agent_id)
    engine.execute(update)


@app.post("/terminal/execute")
async def execute_terminal_command(command: TerminalCommand):

    return {
        "command": command.command,
        "agent_id": command.agent_id,
        "output": f"Executed command '{command.command}' on agent {command.agent_id}",
        "success": True,
        "timestamp": "2024-01-01T10:00:00Z"
    }

@app.get("/health")
async def health_check():

    return {
        "status": "healthy", 
        "message": "Nexus Control API is running",
        "server_running": server.is_running if server else False,
        "database_connected": engine is not None
    }

@app.get("/system/info")
async def get_system_info():

    return {
        "platform": "Windows",
        "python_version": "3.11+",
        "fastapi_version": "0.104.0",
        "database": "SQLite",
        "frontend": "Next.js",
        "tcp_server_host": Config.HOST,
        "tcp_server_port": Config.PORT
    }


app.mount("/", StaticFiles(directory=Config.FRONTEND_BUILD_PATH, html=True), name="static")
