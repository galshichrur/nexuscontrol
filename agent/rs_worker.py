import os
import sys
import socket
import json
import time
from data import get_system_info

SERVER_HOST = sys.argv[1]
SERVER_PORT = int(sys.argv[2])
BUFFER_SIZE = 1024
AGENT_ID_FILENAME = "uuid.txt"
RECV_TIMEOUT = 60
RETRY_CONNECT_INTERVAL = 5

def read_uuid() -> str | None:

    if os.path.exists(AGENT_ID_FILENAME):
        with open(AGENT_ID_FILENAME, "r") as f:
            data = f.read()
            if data:
                return data
            else:
                return None

    return None

def run_command(command: str) -> tuple[str, str]:
    return "helllo", "/"

def communicate(s: socket.socket, initial_connection_info: dict) -> None:

    # Read agent_id
    agent_id = read_uuid()
    if agent_id:
        initial_connection_info["agent_id"] = agent_id

    # Send system info
    raw_data = json.dumps(initial_connection_info)
    s.send(raw_data.encode())

    # Receive
    agent_uid = json.loads(s.recv(BUFFER_SIZE).decode().strip())

    # Save to file received agent_id
    with open(AGENT_ID_FILENAME, "w") as f:
        f.write(agent_uid)

    while True:
        try:
            message = json.loads(s.recv(BUFFER_SIZE).decode())

            response_tuple = run_command(message["command"])
            response = {
                "type": "command_response",
                "command_id": message["command_id"],
                "command_response": response_tuple[0],
                "cwd":  response_tuple[1],
            }
            s.send(json.dumps(response).encode())

        except socket.timeout:  # If socket timeout, send heartbeat
            message = {
                "type": "heartbeat",
            }
            s.send(json.dumps(message).encode())
            print("Sent heartbeat")

        except socket.error:  # If connection is closed, retry connecting to server
            print("Connection closed, retrying connection.")
            main()

def connect_to_server(host: str, port: int) -> socket.socket:
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            print("Connection established")
            return s
        except socket.error:
            print("Failed to connect to server, retrying.")
            time.sleep(RETRY_CONNECT_INTERVAL)

def main() -> None:
    s = connect_to_server(SERVER_HOST, SERVER_PORT)
    s.settimeout(RECV_TIMEOUT)
    communicate(s, get_system_info())

if __name__ == '__main__':
    main()