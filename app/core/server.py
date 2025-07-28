import socket
import threading
import json
import time
import uuid
from db.engine import Engine
from db.models import agents_table, agent_id
from db.query import Insert, Select, Update


class Server:
    def __init__(self, db_engine: Engine, buffer_size: int = 1024) -> None:
        self.db_engine: Engine = db_engine
        self.buffer_size: int = buffer_size
        self.socket: socket = None
        self.is_running: bool = False
        self.host: str | None = None
        self.port: int | None = None
        self.server_thread: threading.Thread | None = None
        self.timeout_secs: int = 160
        self.check_offline_agents_time_secs: int = 60

    def start(self, host: str = "0.0.0.0", port: int = 8001) -> None:
        """Binds the server to the given address, and listens for new connections."""

        if self.is_running:
            print("Server is already running.")
            return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen()

        self.is_running = True
        self.host = host
        self.port = port

        print(f"Server successfully started on {host}:{port}.")

        # Accept new connection in separate thread
        self.server_thread = threading.Thread(target=self.accept_new_connections())
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self) -> None:
        """Stops the server from listening for new connections."""

        if not self.is_running:
            print("Server isn't running.")
            return

        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                raise Exception(f"Error closing server socket: {e}")
            self.socket = None

        self.is_running = False
        print("Server stopped.")

    def accept_new_connections(self) -> None:
        while self.is_running:
            try:
                print("Waiting for new connections...")

                client_socket, address = self.socket.accept()
                print(f"New connection from f{address[0]}:{address[1]}.")

                # Handle new connection in a separate thread
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                thread.daemon = True
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    raise Exception(e)

    def handle_client(self, client_socket: socket.socket, address: tuple[str, int]):
        """Handles a new connection."""

        connection_details_json: str = client_socket.recv(self.buffer_size).decode().strip()
        connection_details: dict = json.loads(connection_details_json)

        conn_agent_id = connection_details.get("agent_id")
        if not conn_agent_id:
            # Set new UUID
            conn_agent_id = str(uuid.uuid4())

        data = {
            "agent_id": conn_agent_id,
            "connection_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "disconnect_time": None,
            "status": True,
            "hostname": connection_details.get("hostname", "unknown"),
            "ip_address": address[0],
            "port": str(address[1]),
        }

        # Check if agent exists in the database
        select = Select(agents_table).all().where((agent_id == conn_agent_id))
        exists = list(self.db_engine.execute(select))

        if exists:
            # Update existing agent
            update = Update(agents_table).set({
                "connection_time": data["connection_time"],
                "status": True,
                "hostname": data["hostname"],
                "ip_address": data["ip_address"],
                "port": data["port"],
                "disconnect_time": None
            }).where(agent_id == agent_id)
            self.db_engine.execute(update)
        else:
            # Insert new agent
            insert = Insert(agents_table).values([data])
            self.db_engine.execute(insert)

        self.db_engine.commit()

        print(f"New agent connected successfully at {address[0]}:{address[1]}.\n Assigned agent ID: {conn_agent_id}.")

        # Send back the assigned agent_id
        client_socket.send(json.dumps(conn_agent_id).encode())