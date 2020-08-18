import base64
import time
import contextlib
import logging

import select
import socket


logging.basicConfig(level=logging.DEBUG)

# Changing the buffer_size and delay, you can improve the speed and bandwidth.
# But if the buffer is too large or the delay is too low, things can break.
BUFFER_SIZE = 4096
DELAY = 0.0001
MAX_ERRORS = 100


def connect_upstream(host, port):
    forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        forward.connect((host, port))
        return forward
    except Exception as e:
        logging.exception(e)
        return False


def find_free_port():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.getsockname()[1]


class Server:
    def __init__(
        self, upstream_host, upstream_port, host="127.0.0.1", port=None, username="", password="", headers=None
    ):
        self.channel = {}
        self.headers = headers or {}
        self.host = host
        self.input_list = []
        self.port = port or find_free_port()
        self.server = None
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port

        if username or password:
            auth = f"{username}:{password}".encode("utf8")
            auth_header = "Basic " + base64.b64encode(auth).decode("utf8")
            self.headers["Proxy-Authorization"] = auth_header

    def on_accept(self):
        forward = connect_upstream(self.upstream_host, self.upstream_port)
        clientsock, clientaddr = self.server.accept()
        if forward:
            logging.debug("%s has connected", clientaddr)
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock
        else:
            logging.warning("Can't establish connection with remote server.")
            logging.warning("Closing connection with client side %s", clientaddr)
            clientsock.close()

    def on_close(self, connection):
        logging.debug("%s has disconnected", connection.getpeername())

        self.input_list.remove(connection)
        self.input_list.remove(self.channel[connection])

        # close the connection with client
        out = self.channel[connection]
        self.channel[out].close()  # equivalent to do connection.close()

        # close the connection with remote server
        self.channel[connection].close()

        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[connection]

    def on_recv(self, connection, data):
        """Injects headers into requests and forwards the connection."""
        head, _, body = data.partition(b"\r\n\r\n")
        if any(
            head.startswith(method)
            for method in [b"CONNECT", b"GET", b"OPTIONS", b"POST", b"HEAD", b"PUT", b"PATCH", b"DELETE"]
        ):
            decoded_head = head.decode("utf8").split("\r\n")
            request = decoded_head[0]
            headers = {t[0]: t[1] for t in map(lambda x: x.split(": ") + [""], decoded_head[1:])}
            new_headers = {**headers, **self.headers}
            new_data = (
                "\r\n".join([request] + [": ".join(h) for h in new_headers.items()] + ["", ""]).encode("utf8") + body
            )
            data = new_data

        self.channel[connection].send(data)

    def run(self):
        """Run the server and try to automatically recover if a connection is dropped."""
        error_count = 0
        while error_count < MAX_ERRORS:
            try:
                self._run()
            except Exception:
                error_count += 1
                self.shutdown()
            except BaseException as e:
                self.shutdown()
                raise e

    def shutdown(self):
        for connection in self.input_list.copy():

            if connection not in self.input_list:
                # Deleting a client connection also removes its upstream connection, so
                # it's tricky to predict how this list will be emptied.

                # Include this check to avoid logging errors.
                continue

            try:
                connection.shutdown(socket.SHUT_RDWR)  # Forces the TCP connection to be dropped.
                self.on_close(connection)
            except Exception as e:
                logging.warning(e)

    def _run(self):
        """Poll the sockets for connections and forward them."""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Stop the port being left bound to this socket after it's closed
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen()
        logging.info(f"Listening on {self.host}:{self.port}")

        self.input_list.append(self.server)
        while True:
            time.sleep(DELAY)
            inputready, _, _ = select.select(self.input_list, [], [])
            for connection in inputready:
                if connection == self.server:
                    self.on_accept()
                    break

                data = connection.recv(BUFFER_SIZE)
                if data:
                    self.on_recv(connection, data)
                else:
                    self.on_close(connection)
                    break


if __name__ == "__main__":
    Server("163.172.222.64", 5836).run()
