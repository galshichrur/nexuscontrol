import uvicorn
from config import Config

if __name__ == '__main__':
    uvicorn.run("app:app", host=Config.API_HOST, port=int(Config.API_PORT), log_level="info")

