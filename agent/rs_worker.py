import os
import sys
import socket
import json

SERVER_HOST: str = sys.argv[0]
SERVER_PORT: int = int(sys.argv[1])
BUFFER_SIZE: int = 1024
SEPARATOR = "<sep>"

def connect() -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_HOST, SERVER_PORT))

    data = {
        "cwd": os.getcwd(),
    }

    s.send(json.dumps(data).encode().strip())