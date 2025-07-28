import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DB_PATH = os.getenv("DB_PATH", "db/nexus_control.db")
    
    # TCP Server
    HOST = os.getenv("TCP_SERVER_HOST", "0.0.0.0")
    PORT = int(os.getenv("TCP_SERVER_PORT", "8080"))
    
    # Frontend
    FRONTEND_BUILD_PATH = os.getenv("FRONTEND_BUILD_PATH", "../frontend/out")
    
    # CORS
    ALLOWED_ORIGINS = [
        "http://0.0.0.0:3000",
    ]
    
    # API
    API_PREFIX = "/api"
    API_TITLE = "Nexus Control API"
    API_VERSION = "0.1.0" 