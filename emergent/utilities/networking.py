import socket

def get_open_port():
    s = socket.socket()
    s.bind(('', 0))            # Bind to a free port provided by the host.
    return s.getsockname()[1]  # Return the port number assigned.

def get_address():
    return socket.gethostbyname(socket.gethostname())

def get_local_addresses():
    addresses = [i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None)]
    addresses.append('127.0.0.1')
    return addresses
