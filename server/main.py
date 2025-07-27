from fastapi import FastAPI
from db.engine import Engine

engine: Engine = Engine()
app = FastAPI(title="Nexus Control", version="0.1.0")

@app.on_event("startup")
async def on_startup():

    # Init DB
    engine.open("nexuscontrol.db")

@app.on_event("shutdown")
async def on_shutdown():

    # Close DB
    engine.commit()
    engine.close()

@app.get("/")
async def root():
    return {"status": "NexusControl server is online."}