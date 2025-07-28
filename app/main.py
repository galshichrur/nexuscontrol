from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from db.engine import Engine
from core.server import Server
from dotenv import load_dotenv
import os


load_dotenv()

engine: Engine = Engine()
server: Server = Server()

app = FastAPI(title="Nexus Control", version="0.1.0")
app.mount("/", StaticFiles(directory="../frontend/out", html=True), name="static")

@app.on_event("startup")
async def on_startup():

    # Init DB
    engine.open(os.getenv("DB_PATH"))

    # Start server
    server.start()

@app.on_event("shutdown")
async def on_shutdown():

    # Close DB
    engine.commit()
    engine.close()
