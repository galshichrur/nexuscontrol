import socket
import threading


class Server:
    def __init__(self) -> None:

        self.socket: socket = None
        self.connected_clients = {}
        self.is_running = False
        self.host = None
        self.port = None
        self.new_connection_time = 1
        self.server_thread = None

    def start(self, host: str, port: int) -> None:
        """Binds the server to the given address, and listens for new connections."""

        if self.is_running:
            return

        self.socket = socket.socket()
        self.socket.bind((host, port))
        self.socket.listen()

        self.is_running = True
        self.host = host
        self.port = port

        # Accept new connection in separate thread
        self.server_thread = threading.Thread(target=self.accept_new_connections())
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        """Stops the server from listening for new connections."""

        if not self.is_running:
            raise Exception("Server isn't running.")


        self.is_running = False


    def accept_new_connections(self):
        while self.is_running:
            try:
                client_socket, address = self.socket.accept()
            except socket.timeout:
                pass

    def handle_client(self, client_socket: socket.socket, address: tuple[str, int]):
        ...
