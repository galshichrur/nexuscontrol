import socket
import threading
import json
from db.engine import Engine
from db.models import agents_table
from db.query import Insert


class Server:
    def __init__(self, db_engine: Engine, buffer_size: int = 1024) -> None:
        self.db_engine: Engine = db_engine
        self.buffer_size: int = buffer_size
        self.socket: socket = None
        self.connected_clients = {}
        self.is_running: bool = False
        self.host: str | None = None
        self.port: int | None = None
        self.new_connection_time: int = 1
        self.server_thread: threading.Thread | None = None

    def start(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Binds the server to the given address, and listens for new connections."""

        if self.is_running:
            raise Exception("Server is already running.")

        self.socket = socket.socket()
        self.socket.bind((host, port))
        self.socket.listen()

        self.is_running = True
        self.host = host
        self.port = port

        # Accept new connection in separate thread
        self.server_thread = threading.Thread(target=self.accept_new_connections())
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        """Stops the server from listening for new connections."""

        if not self.is_running:
            raise Exception("Server isn't running.")


        self.is_running = False

    def accept_new_connections(self):
        while self.is_running:
            try:
                client_socket, address = self.socket.accept()

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

        print(f"New connection from {address}")

        connection_details_json: str = client_socket.recv(self.buffer_size).decode().strip()
        connection_details: dict = json.loads(connection_details_json)

        data = {
            "hostname": connection_details["hostname"],
            "ip": address[0],
            "port": address[1]
        }

        # Insert new client to agent table in db.
        insert = Insert(agents_table).values(
            [data]
        )
        self.db_engine.execute(insert)
        self.db_engine.commit()

        try:
            while self.is_running:
                data = client_socket.recv(self.buffer_size)
                if not data:
                    break

        finally:
            client_socket.close()
