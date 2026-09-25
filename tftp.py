#!/usr/bin/env python3
import argparse
import time
import os
import re
import logging # set log level for fbtftp
from fbtftp.base_handler import BaseHandler
from fbtftp.base_handler import ResponseData
from fbtftp.base_server import BaseServer

SHIM_PATTERN = re.compile(r"(\S+)-shim\S*\.([Ee][Ff][Ii])$")

# client ip -> (timestamp, next_file)
client_states = {}

class FileResponseData(ResponseData):
    # No unpicklable objects in the constructor: fbtftp builds this in the parent
    # process, and Python 3.14 made forkserver the default start method on Linux,
    # which pickles it. Hence open on first read; the stat stays so a missing file
    # still raises FileNotFoundError here.
    def __init__(self, path):
        self._path = path
        self._size = os.stat(path).st_size
        self._reader = None

    def read(self, n):
        if self._reader is None:
            self._reader = open(self._path, 'rb')
        return self._reader.read(n)

    def size(self):
        return self._size

    def close(self):
        if self._reader is not None:
            self._reader.close()

def print_session_stats(stats):
    pass

def print_server_stats(stats):
    pass

class ShimWorkaroundHandler(BaseHandler):
    def __init__(self, server_addr, peer_addr, path, options, root, timeout):
        self._root = root
        real_path = self._resolve_path(peer_addr[0], path)
        super().__init__(server_addr, peer_addr, real_path, options, print_session_stats)

        self._clean_clients(timeout)

    def _clean_clients(self, timeout):
        now = time.time()
        timedout = []
        for ip, state in client_states.items():
            if now - state[0] > timeout:
                timedout.append(ip)

        for ip in timedout:
            client_states.pop(ip)

    def _resolve_path(self, ip, requested_path):
        if ip not in client_states:
            match = SHIM_PATTERN.match(requested_path)
            if match:
                next_file = match.group(1) + '.' + match.group(2)
                client_states[ip] = (time.time(), next_file)
        elif requested_path == "ipxe.efi":
            state = client_states[ip]
            del client_states[ip]
            logging.info(f"SHIM workaround triggered for {state[1]}")
            return state[1]

        return requested_path

    def get_response_data(self):
        path = os.path.abspath(os.path.join(self._root, self._path.lstrip('/')))
        if not path.startswith(os.path.abspath(self._root)):
            raise PermissionError("Access denied: path outside root")

        return FileResponseData(path)

class ShimWorkaroundServer(BaseServer):
    def __init__(self, address, port, retries, timeout, root):
        self._root = root
        super().__init__(address, port, retries, timeout, print_server_stats)

    def get_handler(self, server_addr, peer_addr, path, options):
        return ShimWorkaroundHandler(
            server_addr, peer_addr, path, options, self._root, self._timeout
        )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read-only TFTP server that works around iPXE shim '
                    'binaries resolving their payload by filename.')
    parser.add_argument('--root', default='/srv/pxe',
                        help='directory to serve (default: %(default)s)')
    parser.add_argument('--address', default='::',
                        help='address to bind (default: %(default)s)')
    parser.add_argument('--port', type=int, default=69,
                        help='port to bind (default: %(default)s)')
    parser.add_argument('--timeout', type=int, default=5,
                        help='session timeout in seconds (default: %(default)s)')
    args = parser.parse_args()

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    server = ShimWorkaroundServer(
        address=args.address, port=args.port, retries=3, timeout=args.timeout,
        root=args.root
    )
    try:
        server.run()
    except KeyboardInterrupt:
        server.close()
