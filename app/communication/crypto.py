import os
import socket
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization


class Crypto:

    KEY_LENGTH = 32

    @staticmethod
    def handshake(agent_public_key: bytes) -> tuple[bytes, bytes]:
        """
        Derives a shared key with the agent using X25519 ECDH and HKDF, returns the secret shared
        key and the server’s public key to send back.
        """

        # Generate private and public keys.
        private_key = X25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Calculate shared key
        shared_key = private_key.exchange(X25519PublicKey.from_public_bytes(agent_public_key))

        # Perform key derivation.
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=Crypto.KEY_LENGTH,
            salt=None,
            info=b'handshake data',
        ).derive(shared_key)

        return derived_key, public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)

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
        nonce = packet[:12]
        ct = packet[12:]
        pt = Crypto.decrypt(key, ct, nonce)
        return pt