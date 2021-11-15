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


def send_string(sock,string_tosend):
    sock.sendall(string_tosend.encode() + b'\n')


def send_int(sock,integer_tosend):
    sock.sendall(str(integer_tosend).encode() + b'\n')

# on first server's run, create client's main folder if not created previously.
def create_main_directory():
    if not os.path.exists(PATH):
        os.mkdir(PATH)


# verify if client is an existing client.
def verify_existing_client(client_id):
    if os.path.exists(get_client_path(client_id)):
        return True
    return False


# return client's path by providing an id.
def get_client_path(client_id):
    return PATH + '/' + client_id


# generate new ID using characters and numbers.
def generate_id():
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    generated_id = ''.join(random.choice(characters) for i in range(128))
    os.mkdir(PATH + '/' + generated_id)
    return generated_id


# per request create requested file.
def pull_new_file(client_path):

    relative_path = clientfile.readline().strip().decode()
    file_name = relative_path.split('/')[-1]
    relative_path = relative_path[0:relative_path.find(file_name)]

    if not os.path.exists(client_path + relative_path):
        os.makedirs(client_path + relative_path)

    print(client_path + relative_path + file_name)
    file_size = int(clientfile.readline())
    byte_stream = clientfile.read(file_size)
    with open(os.path.join(client_path, relative_path, file_name), 'wb') as f:
        f.write(byte_stream)


# If client is an existing client, push all data in server's folder to client.
def push_data_existing_client(existing_client_id):
    # get client's folder path.
    client_path = get_client_path(existing_client_id)
    # count number of files in folder.
    num_files = sum(len(files) for _, _, files in os.walk(client_path))
    # send client number of files to expect.
    send_int(client_socket, num_files)
    time.sleep(1)
    # for each file - send relative path, file's size and data.
    for root, dirs, files in os.walk(client_path):
        for name in files:
            # get relative path by removing the prefix.
            relative_path = os.path.join(root[len(client_path):], name)
            send_string(client_socket, relative_path)
            time.sleep(1)
            # send size of the data expected to be sent.
            send_int(client_socket, os.path.getsize(client_path + relative_path))
            time.sleep(1)
            # send all file's data to client.
            with open(os.path.join(client_path, relative_path), 'rb') as f:
                client_socket.sendall(f.read())

            time.sleep(1)

    list_of_empty_dirs = list()
    for (dirpath, dirnames, filenames) in os.walk(PATH):
        if len(dirnames) == 0 and len(filenames) == 0:
            list_of_empty_dirs.append(dirpath[len(client_path):])

    time.sleep(1)
    send_int(client_socket, len(list_of_empty_dirs))
    time.sleep(1)
    for empty_dir in list_of_empty_dirs:
        send_string(client_socket, empty_dir)
        time.sleep(1)


# if client is a new client - create client's folder and pull all client's data to folder.
def pull_data_new_client(client_id):
    client_path = get_client_path(client_id)
    # get number of files expected to be received.
    numFiles = int(clientfile.readline().decode())
    # iterate over all files and write them to folder.
    print(numFiles)
    for indexFile in range(numFiles):
        # receive each file.
        pull_new_file(client_path)
    num_empty_dirs = int(clientfile.readline().decode())
    for i in range(num_empty_dirs):
        os.makedirs(client_path + clientfile.readline().strip().decode())


# per request delete requested file.
def pull_delete_file(client_path):
    relative_path = clientfile.readline().strip().decode()
    if os.path.exists(client_path + relative_path):
        os.remove(client_path + relative_path)


def pull_delete_dir(client_path):
    relative_path = clientfile.readline().strip().decode()
    if os.path.exists(client_path + relative_path):
        os.removedirs(client_path + relative_path)


def check_update(client_id, comment):
    global dict
    client_path = get_client_path(client_id)
    if comment == b'UPDATE_TIME':
        send_string(client_socket, dict[client_id])
        time.sleep(1)
        comment = clientfile.readline().strip().decode()
        if comment == b'PULL_ALL':
            push_data_existing_client(client_id)
    # if NEW_FILE comment received - move to creating requested file.
    elif comment == b'NEW_FILE':
        pull_new_file(client_path)
        dict[client_id] = str(time.time())
    elif comment == b'NEW_DIR':
        os.makedirs(client_path + clientfile.readline().strip().decode())
        dict[client_id] = str(time.time())
    # if DELETE_FILE comment received - move to deleting requested file.
    elif comment == b'DELETE_FILE':
        pull_delete_file(client_path)
        dict[client_id] = str(time.time())
    elif comment == b'DELETE_DIR':
        pull_delete_dir(client_path)
        dict[client_id] = str(time.time())


create_main_directory()
dict = {}
# Main loop of the program will run as long as server is up.
while True:
    # Accept new client.
    client_socket, client_address = server.accept()
    with client_socket, client_socket.makefile('rb') as clientfile:
        # Receive client ID.
        client_id = clientfile.readline().strip().decode()
        print(client_id)
        # verify received id - if exists push all folders to client, otherwise create new client and pull data.
        if verify_existing_client(client_id):
            comment = clientfile.readline().strip()
            if comment == b'SYN_DATA':
                push_data_existing_client(client_id)
            else:
                check_update(client_id, comment)
        else:
            client_id = generate_id()
            send_string(client_socket, client_id)
            pull_data_new_client(client_id)
            dict[client_id] = str(time.time())

