from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from db.engine import Engine
from db.models import agents_table
from db.query import Create
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
    init_db()

    # Start server
    server.start()

def init_db() -> None:
    engine.open(os.getenv("DB_PATH"))
    create = Create(agents_table, exists_ok=True)
    engine.execute(create)
    engine.commit()

@app.on_event("shutdown")
async def on_shutdown():

    # Close DB
    engine.commit()
    engine.close()
