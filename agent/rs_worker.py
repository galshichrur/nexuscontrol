import os
import sys
import socket
import json
import time
from data import connection_details

SERVER_HOST: str = sys.argv[1]
SERVER_PORT: int = int(sys.argv[2])
BUFFER_SIZE: int = 1024
SEPARATOR: str = "<sep>"
AGENT_ID_FILENAME = "uuid.txt"
SLEEP_INTERVAL: float = 120


def get_uuid(s: socket.socket) -> str:

    if os.path.exists(AGENT_ID_FILENAME):
        with open(AGENT_ID_FILENAME, "r") as f:
            data = f.read().strip()
            if data:
                return data
            else:
                return write_to_file(s)

    return write_to_file(s)

def write_to_file(s: socket.socket) -> str:
    uid = first_time_connect(s)
    with open(AGENT_ID_FILENAME, "w") as f:
        f.write(uid)
    print(uid)
    return uid

def first_time_connect(s: socket.socket) -> str:
    data: str = json.dumps(connection_details)

    # Send connection details to server
    s.send(data.encode())

    # Receive assigned agent_id
    return s.recv(BUFFER_SIZE).decode()

def ping(agent_id: str, s: socket.socket) -> None:

    while True:
        time.sleep(SLEEP_INTERVAL)

        # Add agent_id to connection details.
        data = connection_details
        data["agent_id"] = agent_id

        s.send(json.dumps(data).encode().strip())
        print(f"Sent ping {data}")

def main() -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_HOST, SERVER_PORT))
    agent_id = get_uuid(s)
    ping(agent_id, s)

if __name__ == '__main__':
    main()