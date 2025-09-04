
class Config:

    # Database
    DB_PATH = "db/nexuscontrol.db"
    
    # TCP Server
    HOST = "0.0.0.0"
    PORT = 8080
    
    # Frontend
    FRONTEND_BUILD_PATH = "../frontend/out"
    
    # CORS
    ALLOWED_ORIGINS = [
        "http://127.0.0.1:3000",
    ]
    
    # API
    API_PREFIX = "/api"
    API_TITLE = "Nexus Control API"
    API_VERSION = "0.1.0"

    # Logs
    LOGS_PATH = "logs"

    # Server Configuration
    SERVER_RECV_HEARTBEAT_TIMEOUT = 105
    CMD_EXECUTE_TIMEOUT = 25
    MAX_CONNECTIONS = 1
