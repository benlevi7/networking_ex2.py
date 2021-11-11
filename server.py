# Itay Etelis 209041474
# Ben Levi 318811304

import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(('', 12345))

server.listen(5)

while True:
    client_socket, client_address = server.accept()
    print('Connection from: ', client_address)

    data = client_socket.recv(100)
    print('Received: ', data)

    client_socket.send(data.upper())

    client_socket.close()
    print('Client disconnected')
