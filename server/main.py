from fastapi import FastAPI
from db.engine import Engine


app = FastAPI(title="Nexus Control", version="0.1.0")

@app.on_event("startup")
async def on_startup():

    print("Starting Nexus Control...")

    # Init DB
    engine: Engine = Engine().open("nexuscontrol.db")

@app.on_event("shutdown")
async def on_shutdown():
    pass