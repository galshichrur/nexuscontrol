import uvicorn
from config import Config

if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=int(Config.API_PORT), log_level="info")

