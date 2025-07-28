from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from db.engine import Engine
from db.models import agents_table
from db.query import Create
from server import Server
from config import Config
from api.routes import router as api_router


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

    engine.open(Config.DB_PATH)
    create = Create(agents_table, exists_ok=True)
    engine.execute(create)
    engine.commit()

    print("Database initialized.")

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
app.include_router(api_router, prefix=Config.API_PREFIX)

app.mount("/", StaticFiles(directory=Config.FRONTEND_BUILD_PATH, html=True), name="static")