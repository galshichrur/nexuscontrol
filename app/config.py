import os
from dotenv import load_dotenv


load_dotenv("./.env")

class Config:

    # Database
    DB_PATH = os.getenv("DB_PATH")
    
    # TCP Server
    HOST = os.getenv("SERVER_HOST")
    PORT = int(os.getenv("SERVER_PORT"))
    
    # Frontend
    FRONTEND_BUILD_PATH = os.getenv("FRONTEND_BUILD_PATH")

    # API
    API_PREFIX = os.getenv("API_PREFIX")
    API_TITLE = os.getenv("API_TITLE")
    API_VERSION = os.getenv("API_VERSION")

    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS").split(",")

    # Logs
    LOGS_PATH = os.getenv("LOGS_PATH")

    # Server Settings
    SERVER_RECV_HEARTBEAT_TIMEOUT = int(os.getenv("SERVER_RECV_HEARTBEAT_TIMEOUT"))
    CMD_EXECUTE_TIMEOUT = int(os.getenv("CMD_EXECUTE_TIMEOUT"))
    MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS"))

    PE_FILE_PATH = os.getenv("PE_FILE_PATH")
    PE_FILE_NAME = os.getenv("PE_FILE_NAME")
    REGULAR_FILE_PATH = os.getenv("REGULAR_FILE_PATH")
    REGULAR_FILE_NAME = os.getenv("REGULAR_FILE_NAME")
