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



def check_update(client_id, comment):
    client_path = get_client_path(client_id)
    if comment == 'UPDATE_TIME':
        utils.send_string(client_socket, dict[client_id])
        time.sleep(1)
        comment = client_file.readline().strip().decode()
        if comment == 'PULL_ALL':
            utils.push_data(client_socket, client_path)
    # if NEW_FILE comment received - move to creating requested file.
    elif comment == 'NEW_FILE':
        utils.pull_new_file(client_file, client_path)
        dict[client_id] = str(time.time())
    elif comment == 'NEW_DIR':
        os.makedirs(utils.join_path_relativepath(client_file.readline().strip().decode(), client_path), exist_ok=True)
        dict[client_id] = str(time.time())
    # if DELETE_FILE comment received - move to deleting requested file.
    elif comment == 'DELETE':
        utils.pull_delete_file(client_file, client_path)
        dict[client_id] = str(time.time())


create_main_directory()
dict = {}
# Main loop of the program will run as long as server is up.
while True:
    # Accept new client.
    client_socket, client_address = server.accept()
    with client_socket, client_socket.makefile('rb') as client_file:
        # Receive client ID.
        client_id = client_file.readline().strip().decode()
        print(client_id)
        # verify received id - if exists push all folders to client, otherwise create new client and pull data.
        if verify_existing_client(client_id):
            comment = client_file.readline().strip().decode()
            if comment == 'SYN_DATA':
                utils.push_data(client_socket, get_client_path(client_id))
            else:
                check_update(client_id, comment)
        else:
            client_id = generate_id()
            dict[client_id] = str(time.time())
            utils.send_string(client_socket, client_id)
            utils.pull_data(client_file, get_client_path(client_id))

        client_file.close()
