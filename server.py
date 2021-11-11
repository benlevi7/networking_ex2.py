# Itay Etelis 209041474
# Ben Levi 318811304
import random
import socket
import string
import sys
import os
import time

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = int(sys.argv[1])
PATH = os.path.abspath(os.getcwd()) + '/Clients'
server.bind(('', PORT))
server.listen(1)


def createFolder() :
    if not os.path.exists(PATH):
        os.mkdir(PATH)


def givePath(id):
    return PATH + '/' + id


def getId():
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    id = ''.join(random.choice(characters) for i in range(128))
    os.mkdir(PATH + '/' + id)
    return id


def newClient():
    clientId = getId()
    client_socket.send(clientId.encode('utf8'))
    clientPath = givePath(clientId)

    numFiles = int.from_bytes(client_socket.recv(1024), 'little')

    for indexFile in range(numFiles):
        reativePath = client_socket.recv(1024).decode('utf8')

        file = open(clientPath + reativePath, "wb")

        fileSize = int.from_bytes(client_socket.recv(1024), 'little')
        tempSize = 0

        while tempSize < fileSize:
            data = client_socket.recv(1024)
            tempSize += len(data)
            file.write(data)
        file.close()


def existClient(id):
    clientPath = givePath(id.decode('utf8'))
    numFiles = sum(len(files) for _, _, files in os.walk(clientPath))
    client_socket.send(int.to_bytes(numFiles, 4, 'little'))
    time.sleep(1)
    for root, dirs, files in os.walk(clientPath):
        for name in files:
            relativePath = os.path.join(root[len(clientPath):], name)
            client_socket.send(relativePath.encode('utf8'))
            time.sleep(1)
            client_socket.send(int.to_bytes(os.path.getsize(clientPath + '/' + relativePath), 4, 'little'))
            time.sleep(1)

            file = open(clientPath + '/' + relativePath, "rb")
            file_data = file.read(1024)
            while file_data:
                client_socket.send(file_data)
                file_data = file.read(1024)
            file.close()



while True:
    client_socket, client_address = server.accept()
    data = client_socket.recv(1024)
    if len(data.decode('utf8')) != 128:
        newClient()
    else:
        existClient(data)


    client_socket.close()
