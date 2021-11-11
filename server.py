# Itay Etelis 209041474
# Ben Levi 318811304

import socket
import sys
import os

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = int(sys.argv[1])
PATH = path = os.path.abspath(os.getcwd()) + '/Clients'
server.bind(('', PORT))
server.listen(1)
def createFolder() :
    if not os.path.exists(PATH):
        os.mkdir(path)

def checkId(id) :
    listId = os.listdir(PATH)
    for name in listId:
        if name == id:
            return True
    return False

def getId():


while True:
    client_socket, client_address = server.accept()
    data = client_socket.recv(1024)
    if not checkId(data):
        newId = getId()

    client_socket.send(data.upper())

    client_socket.close()
