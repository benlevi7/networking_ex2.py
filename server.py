# Itay Etelis 209041474
# Ben Levi 318811304
import random
import socket
import string
import sys
import os

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

def newClient() :
    clientId = getId()
    client_socket.send(bytes(clientId))
    clientPath = givePath(clientId)




def existClient():
    clientPath = givePath(data.decode('utf8'))



while True:
    client_socket, client_address = server.accept()
    data = client_socket.recv(1024)
    if len(data.decode('utf8')) != 128:
        newClient()
    else:
        existClient()

    client_socket.close()
