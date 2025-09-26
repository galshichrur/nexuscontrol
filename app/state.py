from typing import Optional
from db.engine import Engine
from communication.server import Server


db_engine: Optional[Engine] = None
server: Optional[Server] = None
