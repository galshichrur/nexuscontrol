import state
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from db.engine import Engine
from db.models import agents_table
from db.query import Create
from communication.server import Server
from config import Config
from logs import logger
from api.endpoints import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Init DB
    state.db_engine = Engine()
    state.db_engine.open(Config.DB_PATH)
    create = Create(agents_table, exists_ok=True)
    state.db_engine.execute(create)
    state.db_engine.commit()
    logger.info("Database initialized.")

    # Start server
    state.server = Server(Engine)
    state.server.start(Config.HOST, Config.PORT)

    yield

    # Stop server
    state.server.stop()

    # Close DB
    state.db_engine.commit()
    state.db_engine.close()
    logger.info("Server successfully stopped.")

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

app.include_router(router)
app.mount("/", StaticFiles(directory=Config.FRONTEND_BUILD_PATH, html=True), name="static")
