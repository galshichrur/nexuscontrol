import socket
import threading
import time
import uuid
import os
import logging
from communication.crypto import Crypto
from config import Config
from typing import Type
from db.engine import Engine
from db.models import agents_table, agent_id, status
from db.query import Insert, Select, Update
from logs import logger
from communication.helper import send_secure_json, receive_secure_json


class Server:
    def __init__(self, db_engine_class: Type[Engine]) -> None:
        self.db_engine_class: Type[Engine] = db_engine_class
        self.socket: socket.socket | None = None
        self.is_running: bool = False
        self.host: str | None = None
        self.port: int | None = None
        self.server_thread: threading.Thread | None = None

        self.HEARTBEAT_TIMEOUT: int = Config.SERVER_RECV_HEARTBEAT_TIMEOUT  # Max timeout to wait for agent heartbeats.
        self.CMD_TIMEOUT: int = Config.CMD_EXECUTE_TIMEOUT  # Max timeout to wait for cmd to execute on the agent system.
        self.MAX_CONNECTIONS: int = Config.MAX_CONNECTIONS

        self.connected_agents: dict[str, tuple[socket.socket, bytes]] = {}
        self.pending_agent_responses: dict[str, dict] = {}

    def start(self, host: str = "0.0.0.0", port: int = 8080) -> None:

        if self.is_running:
            logger.error("Server is already running.")
            return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen()

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
                for agent_socket, _ in self.connected_agents.values():
                    agent_socket.close()

                self.connected_agents = {}
                self._set_all_agents_offline()
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

        try:
            # Receive agent-public-key message.
            agent_public_key = client_socket.recv(Crypto.KEY_LENGTH)
            shared_key, server_public_key = Crypto.handshake(agent_public_key)

            # Send server-public-key message.
            client_socket.send(server_public_key)
        except Exception as e:
            logger.error(f"Error receiving agent public key: {e}")
            client_socket.close()
            return

        db_engine_thread = self.db_engine_class()
        db_engine_thread.open(os.getenv("DB_PATH"))
        agent_uuid = None

        try:
            client_socket.settimeout(self.HEARTBEAT_TIMEOUT)  # Set timeout.

            agent_hello: dict = receive_secure_json(client_socket, shared_key)
            if agent_hello.get("type") != "agent-hello":
                raise Exception("Received invalid message type.")

            agent_uuid = agent_hello.get("agent_id")
            if agent_uuid is None:
                agent_uuid = str(uuid.uuid4())

            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            data = {
                "agent_id": agent_uuid,
                "name": agent_hello.get("hostname", "unknown"),
                "connection_time": current_time,
                "host": address[0],
                "port": str(address[1]),
                "status": True,

                "hostname": agent_hello.get("hostname", "unknown"),
                "cwd": agent_hello.get("cwd", "unknown"),
                "os_name": agent_hello.get("os_name", "unknown"),
                "os_version": agent_hello.get("os_version", "unknown"),
                "os_architecture": agent_hello.get("os_architecture", "unknown"),
                "local_ip": agent_hello.get("local_ip", "unknown"),
                "public_ip": agent_hello.get("public_ip", "unknown"),
                "mac_address": agent_hello.get("mac_address", "unknown"),
                "is_admin": agent_hello.get("is_admin", "unknown"),
                "username": agent_hello.get("username", "unknown")
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

            # Construct and send server hello message
            server_hello = {
                "type": "server-hello",
                "agent_id": agent_uuid
            }
            send_secure_json(client_socket, shared_key, server_hello)
            db_engine_thread.commit()

            # Store agent socket and shared key
            self.connected_agents[agent_uuid] = client_socket, shared_key
            logger.info(f"Agent {agent_uuid} is connected and online.")

            # Communication loop
            while self.is_running:
                try:
                    response = receive_secure_json(client_socket, shared_key)

                    if response.get("type") == "response":
                        self.pending_agent_responses[response["response_id"]] = response
                        logging.info(f"Received response from agent {agent_uuid}.")

                    elif response.get("type") == "heartbeat":  # Heartbeat from agent to keep the connection alive.
                        logging.info(f"Server heartbeat received from agent {agent_uuid}.")
                        pass

                except socket.timeout:  # Didn't receive any command or heartbeat.
                    break
                # Agent disconnected.
                except ConnectionResetError or ConnectionError or ConnectionAbortedError or ConnectionRefusedError:
                    break

        except Exception as e:
            logger.error(f"Error handling client {address[0]}:{address[1]}: {e}")
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
            request_id = str(uuid.uuid4())
            agent_socket = self.connected_agents[agent_uid][0]
            if not agent_socket:
                self._set_agent_offline(agent_uid)
                return {
                    "status": False,
                    "response": None,
                    "cwd": None,
                }
            data = {
                "type": "request",
                "request_id": request_id,
                "command": command,
            }
            send_secure_json(agent_socket, self.connected_agents[agent_uid][1], data)

            # Wait for the response to be received.
            elapsed = 0
            while request_id not in self.pending_agent_responses and elapsed < self.CMD_TIMEOUT:
                time.sleep(0.05)
                elapsed += 0.05

            if elapsed >= self.CMD_TIMEOUT:
                return {
                    "status": False,
                    "response": "Error: command timed out.",
                    "cwd": None,
                }

            response_data = self.pending_agent_responses.pop(request_id)
            if response_data:
                return {
                    "status": True,
                    "response": response_data.get("response"),
                    "cwd": response_data.get("cwd"),
                }

            self._set_agent_offline(agent_uid)
            return {
                "status": False,
                "response": None,
                "cwd": None,
            }
        except Exception as e:
            logger.error(f"Unexpected error in interact_with_agent loop: {e}")

    def _set_agent_offline(self, agent_uuid: str) -> None:

        db_engine_thread = self.db_engine_class()
        db_engine_thread.open(os.getenv("DB_PATH"))

        update_query = Update(agents_table).set({status: False}).where(agent_id == agent_uuid)
        db_engine_thread.execute(update_query)

        db_engine_thread.commit()

    def _set_all_agents_offline(self) -> None:

        db_engine_thread = self.db_engine_class()
        db_engine_thread.open(os.getenv("DB_PATH"))

        update_query = Update(agents_table).set({status: False})
        db_engine_thread.execute(update_query)

        db_engine_thread.commit()