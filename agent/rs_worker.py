import os
import sys
import socket
import json
from data import connection_details

SERVER_HOST: str = sys.argv[0]
SERVER_PORT: int = int(sys.argv[1])
BUFFER_SIZE: int = 1024
SEPARATOR: str = "<sep>"
AGENT_ID_FILENAME = "uuid.txt"

def get_uuid() -> str:
    if os.path.exists(AGENT_ID_FILENAME):
        with open(AGENT_ID_FILENAME, "r") as f:
            return f.read().strip()
    else:
        uid = first_time_connect()
        with open(AGENT_ID_FILENAME, "w") as f:
            f.write(uid)
        return uid

def first_time_connect() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_HOST, SERVER_PORT))

    # Send connection details to server
    s.send(json.dumps(connection_details).encode().strip())

    # Receive assigned agent_id
    return s.recv(BUFFER_SIZE).decode().strip()


if __name__ == '__main__':
    agent_id = get_uuid()