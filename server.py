# Itay Etelis 209041474
# Ben Levi 318811304
import random
import socket
import string
import sys
import os
import time
import utils

SEP = os.path.sep
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = int(sys.argv[1])
PATH = os.path.abspath(os.getcwd()) + SEP + 'Clients'
server.bind(('', PORT))
server.listen()


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
    return utils.join_path_relativepath(client_id, PATH)


# generate new ID using characters and numbers.
def generate_id():
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    generated_id = ''.join(random.choice(characters) for i in range(128))
    os.mkdir(utils.join_path_relativepath(generated_id, PATH))
    return generated_id


def send_updates(client_id, client_index):
    list_updates = dict[(client_id, client_index)]
    utils.send_int(client_socket, len(list_updates))
    print('Updates size: -----' + str(len(list_updates)))
    for t in list_updates:
        utils.send_string(client_socket, t[0])
        if t[0] == 'NEW_FILE':
            utils.send_created_file(client_socket, utils.join_path_relativepath(t[1], get_client_path(client_id)), get_client_path(client_id))
        else:
            utils.send_string(client_socket, t[1])

        print('t[0] ==    ' + str(t[0]))
        print('t[1] ==    ' + str(t[1]))
    list_updates.clear()


def add_update(client_id, client_index, comment, src):
    keys = dict.keys()
    for t in keys:
        if t[0] == client_id and t[1] != client_index:
            print(t)
            print('Adding update ' + comment)
            dict[(client_id, t[1])].append((comment, src))


def check_update(client_id, recv_client_index):
    client_path = get_client_path(client_id)
    comment = client_file.readline().strip().decode()
    if comment == 'UPDATE_TIME':
        send_updates(client_id, recv_client_index)
        return
    # if NEW_FILE comment received - move to creating requested file.
    elif comment == 'NEW_FILE':
        src = utils.pull_new_file(client_file, client_path)
        add_update(client_id, recv_client_index, comment, src)
    elif comment == 'NEW_DIR':
        src = client_file.readline().strip().decode()
        os.makedirs(utils.join_path_relativepath(src, client_path), exist_ok=True)
        add_update(client_id, recv_client_index, comment, src)
    # if DELETE_FILE comment received - move to deleting requested file.
    elif comment == 'DELETE':
        src = utils.pull_delete_file(client_file, client_path)
        add_update(client_id, recv_client_index, comment, src)

create_main_directory()
dict = {}
# Main loop of the program will run as long as server is up.
while True:
    # Accept new client.
    client_socket, client_address = server.accept()
    with client_socket, client_socket.makefile('rb') as client_file:
        client_index = str(random.randint(1, sys.maxsize))
        # Receive client ID.
        client_id = client_file.readline().strip().decode()
        print(client_id)
        # verify received id - if exists push all folders to client, otherwise create new client and pull data.
        if verify_existing_client(client_id):
            comment = client_file.readline().strip().decode()
            if comment == 'SYN_DATA':
                dict[(client_id, client_index)] = []
                utils.send_string(client_socket, client_index)
                utils.push_data(client_socket, get_client_path(client_id))
            else:
                check_update(client_id, comment)
        else:
            client_id = generate_id()
            dict[(client_id, client_index)] = []
            utils.send_string(client_socket, client_id)
            utils.send_string(client_socket, client_index)
            utils.pull_data(client_file, get_client_path(client_id))

        client_file.close()
