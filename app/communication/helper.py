import socket
import json
from crypto import Crypto


BUFFER = 2048


def send_secure_json(s: socket.socket, key: bytes, data: dict) -> None:
    """Serializes, encodes, and sends dict as json securely."""

    json_data = json.dumps(data).encode()
    Crypto.send_secure(s, key, json_data)

def receive_secure_json(s: socket.socket, key: bytes) -> dict | None:
    """Receives and decodes data to dict securely."""

    data = Crypto.receive_secure(s, key)
    return json.loads(data.decode())