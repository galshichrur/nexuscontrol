import socket
import threading
import json
import time
import uuid
import os
import logging
from typing import Type
from db.engine import Engine
from db.models import agents_table, agent_id
from db.query import Insert, Select, Update
from logs import logger



class Server:
    def __init__(self, db_engine_class: Type[Engine], buffer_size: int = 1024) -> None:
        self.db_engine_class: Type[Engine] = db_engine_class
        self.buffer_size: int = buffer_size
        self.socket: socket = None
        self.is_running: bool = False
        self.host: str | None = None
        self.port: int | None = None
        self.server_thread: threading.Thread | None = None
        self.timeout_secs: int = 160
        self.check_offline_agents_time_secs: int = 60
        self.max_connections: int = 5

    def start(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """Binds the server to the given address, and listens for new connections."""

        if self.is_running:
            logger.error("Server is already running.")
            return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen(self.max_connections)

        self.is_running = True
        self.host = host
        self.port = port

        logging.info(f"Server successfully started on {host}:{port}.")

        # Accept new connection in separate thread
        self.server_thread = threading.Thread(target=self.accept_new_connections)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self) -> None:
        """Stops the server from listening for new connections."""

        if not self.is_running:
            logger.error("Server isn't running.")
            return

        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                raise Exception(f"Error closing server socket: {e}")
            self.socket = None

        self.is_running = False
        logger.info("Server stopped.")

    def accept_new_connections(self) -> None:

        while self.is_running:
            try:
                client_socket, address = self.socket.accept()
                logger.info(f"New connection from {address[0]}:{address[1]}.")

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

        logger.info(f"Stated handling new connection: {address[0]}:{address[1]}.")
        db_engine_thread = self.db_engine_class()
        db_engine_thread.open(os.getenv("DB_PATH"))

        try:
            connection_details_json: str = client_socket.recv(self.buffer_size).decode()
            connection_details: dict = json.loads(connection_details_json)

            conn_agent_id = connection_details.get("agent_id")
            if not conn_agent_id:
                # Set new UUID
                conn_agent_id = str(uuid.uuid4())

            data = {
                "agent_id": conn_agent_id,
                "connection_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "status": True,
                "port": str(address[1]),

                "hostname": connection_details.get("hostname", "unknown"),
                "cwd": connection_details.get("cwd", "unknown"),
                "os_name": connection_details.get("os_name", "unknown"),
                "os_version": connection_details.get("os_version", "unknown"),
                "os_architecture": connection_details.get("os_architecture", "unknown"),
                "local_ip": connection_details.get("local_ip", "unknown"),
                "public_ip": connection_details.get("public_ip", "unknown"),
                "mac_address": connection_details.get("mac_address", "unknown"),
                "is_admin": connection_details.get("is_admin", "unknown"),
                "username": connection_details.get("username", "unknown")
            }

            # Check if agent exists in the database
            select = Select(agents_table).where((agent_id == conn_agent_id))
            exists = list(db_engine_thread.execute(select))

            if exists:
                logger.info("Agent already exists, updating connection.")
                # Update existing agent
                update = Update(agents_table).set(data).where(agent_id == conn_agent_id)
                db_engine_thread.execute(update)
            else:
                logger.info("Agent not found, creating new one.")
                # Insert new agent
                insert = Insert(agents_table).values([data])
                db_engine_thread.execute(insert)
                logger.info(f"New agent connected successfully at {address[0]}:{address[1]}.\nAssigned agent ID: {conn_agent_id}.")

            db_engine_thread.commit()

            # Send back the assigned agent_id
            client_socket.send(json.dumps(conn_agent_id).encode())
        except Exception as e:
            logging.log(logging.ERROR, f"Error handling client {address[0]}:{address[1]}: {e}")
        finally:
            db_engine_thread.close()