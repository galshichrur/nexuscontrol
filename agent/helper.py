import socket
import json

BUFFER = 2048


def send_json(s: socket.socket, data: dict) -> None:
    """Serializes, encodes, and sends through socket data with its length."""

    json_data = json.dumps(data).encode()
    msg_len = len(json_data)
    s.send(msg_len.to_bytes(4, byteorder="big") + json_data)


def receive_json(s: socket.socket) -> dict | None:
    """Receives and decodes data from socket with its length."""

    raw_msg_len = s.recv(4)
    if not raw_msg_len:
        return None
    msg_len = int.from_bytes(raw_msg_len, byteorder="big")

    chunks = []
    received_bytes = 0
    while received_bytes < msg_len:
        chunk = s.recv(min(msg_len - received_bytes, BUFFER))
        if not chunk:
            return None
        chunks.append(chunk)
        received_bytes += len(chunk)

    full_message = b"".join(chunks)
    return json.loads(full_message.decode())
