from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from db.engine import Engine
from db.models import agents_table
from db.query import Create
from core.server import Server
from dotenv import load_dotenv
import os

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Init DB
    engine: Engine = Engine()
    init_db(engine)

    # Start server
    server: Server = Server(Engine)
    server.start("127.0.0.1", 8091)

    yield

    # Stop server
    server.stop()

    # Close DB
    engine.commit()
    engine.close()
    print("Server successfully stopped.")

def init_db(engine: Engine) -> None:

    engine.open(os.getenv("DB_PATH"))
    create = Create(agents_table, exists_ok=True)
    engine.execute(create)
    engine.commit()

    print("Database initialized.")

app = FastAPI(title="Nexus Control", version="0.1.0", lifespan=lifespan)
app.mount("/", StaticFiles(directory="../frontend/out", html=True), name="static")