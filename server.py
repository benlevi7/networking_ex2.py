# Itay Etelis 209041474
# Ben Levi 318811304
import random
import socket
import string
import sys
import os
import time
from socket import error as SocketError

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = int(sys.argv[1])
PATH = os.path.abspath(os.getcwd()) + '/Clients'
server.bind(('', PORT))
server.listen()


# on first server's run, create client's main folder if not created previously.
def create_main_directory():
    if not os.path.exists(PATH):
        os.mkdir(PATH)


# verify if client is an existing client.
def verify_existing_client(client_id):
    if os.path.exists(get_client_path(client_id)):
        print('fountID')
        return True
    return False

# return client's path by providing an id.
def get_client_path(client_id):
    return PATH + '/' + client_id


# generate new ID using characters and numbers.
def generate_id():
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    client_id = ''.join(random.choice(characters) for i in range(64))
    os.mkdir(PATH + '/' + client_id)
    return client_id


# per request create requested file.
def pull_new_file(client_path):
    relative_path = client_socket.recv(1024).decode('utf8')
    file_name = relative_path.split('/')[-1]
    relative_path = relative_path[0:relative_path.find(file_name)]

    if not os.path.exists(client_path + relative_path):
        os.makedirs(client_path + relative_path)

    file = open(client_path + relative_path + '/' + file_name, "wb")

    file_size = int.from_bytes(client_socket.recv(1024), 'little')
    temp_size = 0

    while temp_size < file_size:
        byte_stream = client_socket.recv(1024)
        print(byte_stream)
        temp_size += len(byte_stream)
        file.write(byte_stream)
    file.close()


# per request delete requested file.
def pull_delete_file(client_path):
    relative_path = client_socket.recv(1024).decode('utf8')
    if os.path.exists(client_path + relative_path):
        os.remove(client_path + relative_path)


# if client is a new client - create client's folder and pull all client's data to folder.
def pull_data_new_client(client_id):
    client_path = get_client_path(client_id)
    # get number of files expected to be received.
    numFiles = int.from_bytes(client_socket.recv(1024), 'little')
    # iterate over all files and write them to folder.
    for indexFile in range(numFiles):
        # receive each file.
        pull_new_file(client_path)


# If client is an existing client, push all data in server's folder to client.
def push_data_existing_client(client_id):
    # get client's folder path.
    client_path = get_client_path(client_id)
    # count number of files in folder.
    numFiles = sum(len(files) for _, _, files in os.walk(client_path))
    # send client number of files to expect.
    client_socket.send(int.to_bytes(numFiles, 4, 'little'))
    time.sleep(1)
    # for each file - send relative path, file's size and data.
    for root, dirs, files in os.walk(client_path):
        for name in files:
            # get relative path by removing the prefix.
            relative_path = os.path.join(root[len(client_path):], name)
            client_socket.send(relative_path.encode('utf8'))
            time.sleep(1)
            # send size of the data expected to be sent.
            client_socket.send(int.to_bytes(os.path.getsize(client_path + '/' + relative_path), 4, 'little'))
            time.sleep(1)
            # send all file's data to client.
            file = open(client_path + '/' + relative_path, "rb")
            file_data = file.read(1024)
            while file_data:
                client_socket.send(file_data)
                file_data = file.read(1024)
            file.close()


def check_update(client_id, data):
    client_path = get_client_path(client_id)
    if data == b'UPDATE_TIME':
        client_socket.send(dict[client_id])
        data = client_socket.recv(1024)
        if data == b'PULL_ALL':
            push_data_existing_client(client_id)
    # if NEW_FILE comment received - move to creating requested file.
    elif data == b'NEW_FILE':
        pull_new_file(client_path)
        dict[client_id] = str(time.time()).encode('utf8')
    # if DELETE_FILE comment received - move to deleting requested file.
    elif data == b'DELETE_FILE':
        pull_delete_file(client_path)
        dict[client_id] = str(time.time()).encode('utf8')
    # if MOVE_FILE comment received - move to deleting and re-adding requested file.
    elif data == b'MOVE_FILE':
        pull_delete_file(client_path)
        pull_new_file(client_path)
        dict[client_id] = str(time.time()).encode('utf8')


create_main_directory()
dict = {}
# Main loop of the program will run as long as server is up.
while True:
    # Accept new client.
    client_socket, client_address = server.accept()
    # Receive client ID.
    client_id = client_socket.recv(1024).decode('utf-8')
    print(client_id)
    # verify received id - if exists push all folders to client, otherwise create new client and pull data.
    if verify_existing_client(client_id):
        data = client_socket.recv(1024)
        if data == b'SYN_DATA':
            push_data_existing_client(client_id)
        else:
            check_update(client_id, data)
    else:
        print('new_client')
        client_id = generate_id()
        client_socket.send(client_id.encode('utf8'))
        pull_data_new_client(client_id)
        dict[client_id] = str(time.time()).encode('utf8')
    client_socket.close()
