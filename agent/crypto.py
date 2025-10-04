import os
import socket
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class Crypto:

    KEY_LENGTH = 32

    @staticmethod
    def encrypt(key: bytes, data: bytes) -> tuple[bytes, bytes]:
        """
        Encrypts data using AES-GCM. Returns ciphertext, nonce used to encrypt data.
        """

        aes = AESGCM(key)
        nonce = os.urandom(12)
        ct = aes.encrypt(nonce, data, None)
        return ct, nonce

    @staticmethod
    def decrypt(key: bytes, data: bytes, nonce: bytes) -> bytes:
        """
        Decrypts data using AES-GCM. Returns plaintext.
        """

        aes = AESGCM(key)
        pt = aes.decrypt(nonce, data, None)
        return pt

    @staticmethod
    def send_secure(s: socket.socket, key: bytes, data: bytes) -> None:
        """
        Sends a secure message to the agent using shared key with AES-GCM.
        """

        ct, nonce = Crypto.encrypt(key, data)
        packet = nonce + ct
        msg_len = len(packet).to_bytes(4, "big")
        s.sendall(msg_len + packet)

    @staticmethod
    def receive_secure(s: socket.socket, key: bytes) -> bytes:
        """
        Receives a secure message from agent using shared key with AES-GCM.
        Returns received plaintext in bytes.
        """

        msg_len = int.from_bytes(s.recv(4), "big")
        packet = s.recv(msg_len)
        if not packet:
            raise ConnectionResetError("Socket closed.")
        nonce = packet[:12]
        ct = packet[12:]
        pt = Crypto.decrypt(key, ct, nonce)
        return pt