# Itay Etelis 209041474
# Ben Levi 318811304

import random
import socket
import string
import sys
import os
import utils

# initialize variables to hold arguments.
SEP = os.path.sep
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = int(sys.argv[1])
PATH = os.path.abspath(os.getcwd()) + SEP + 'Clients'
server.bind(('', PORT))
server.listen()


# on first server's run, create client's main folder if not created previously.
#   return - none.
def create_main_directory():
    if not os.path.exists(PATH):
        os.mkdir(PATH)


# verify if client is an existing client.
    # @param client_id - id of a given client.
    # return - none.
def verify_existing_client(client_id):
    if os.path.exists(get_client_path(client_id)):
        return True
    return False


# return client's path by providing an id.
    # @param client_id - id of a given client.
    # return - none.
def get_client_path(client_id):
    return utils.join_paths(client_id, PATH)


# generate new ID using characters and numbers.
    # return - none.
def generate_id():
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    generated_id = ''.join(random.choice(characters) for i in range(128))
    os.mkdir(utils.join_paths(generated_id, PATH))
    return generated_id


# send_updates - if client requested an update, send all updates according to client's id and session id.
    # @param client_id - id of a given client.
    # @param client_session_id - session id help distinguish between same client from different systems.
    # return - none.
def send_updates(client_id, client_session_id):
    list_updates = dict[(client_id, client_session_id)]
    # send number of expected updates to be sent.
    utils.send_int(client_socket, len(list_updates))
    # for each update in the list:
    for operation in list_updates:
        # send operation.
        utils.send_string(client_socket, operation[0])
        # if operation is creation of a new file, work accordingly and send the whole file.
        if operation[0] == 'NEW_FILE':
            utils.push_file(client_socket, client_file,
                            utils.join_paths(operation[1], get_client_path(client_id)), get_client_path(client_id))

        # otherwise send the operation as is.
        else:
            utils.send_string(client_socket, operation[1])

    # clear all updates.
    list_updates.clear()


# add_update - add the given update to all client's with corresponding id and different session id.
    # @param client_id - id of a given client.
    # @param client_session_id - session id help distinguish between same client from different systems.
    # @param comment - the comment sent from client, indicating the server what operation is expected to happend.
    # @parm src - src path of given update.
    # return - none.
def add_update(client_id, client_session_id, comment, src):
    # if comment sent from client was indicating a deletion of file or folder.
    if comment == 'DELETE':
        # search for given client in the main queue - make sure previous creation of same file is deleted.
        for operation in dict.keys():
            if operation[0] == client_id and operation[1] != client_session_id:
                flag = 0
                # make sure previous creation of same file is deleted from the queue.
                for update in dict[operation]:
                    if update[0] == 'NEW_FILE' and update[1] == src:
                        dict[operation].remove(update)
                        flag = 1
                if flag == 0:
                    dict[(client_id, operation[1])].append((comment, src))
        return
    # iterate over operation for each system with corresponding client's id and different session id insert given update
    for operation in dict.keys():
        if operation[0] == client_id and operation[1] != client_session_id:
            dict[(client_id, operation[1])].append((comment, src))


# check_update - with given update comment check what update would the client inform the server with.
    # @param client_id - id of a given client.
    # @param client_session_id - session id help distinguish between same client from different systems.
    # @param update - the update sent from client, indicating the server what operation is expected to happen.
    # return - none.
def check_update(client_id, client_session_id, update):
    client_path = get_client_path(client_id)
    # if UPDATE_TIME comment received - move to sending all updates to client.
    if update == 'UPDATE_TIME':
        send_updates(client_id, client_session_id)
        return

    # if NEW_FILE comment received - move to creating requested file.
    elif update == 'NEW_FILE':
        src = utils.pull_new_file(client_socket, client_file, client_path)
        add_update(client_id, client_session_id, update, src)

    # if NEW_DIR comment received - move to creating new folder.
    elif update == 'NEW_DIR':
        src = utils.replace_separators(client_file.readline().strip().decode())
        if not os.path.exists(utils.join_paths(src, client_path)):
            os.makedirs(utils.join_paths(src, client_path), exist_ok=True)
            add_update(client_id, client_session_id, update, src)

    # if DELETE_FILE comment received - move to deleting requested file
    elif update == 'DELETE':
        src = utils.pull_delete_file(client_file, client_path)
        add_update(client_id, client_session_id, update, src)

    # if CHANGE comment received - move to deleting and creation a new file.
    elif update == 'CHANGE':
        update = client_file.readline().strip().decode()  # 'DELETE'
        check_update(client_id, client_session_id, update)
        update = client_file.readline().strip().decode()  # 'NEW'
        check_update(client_id, client_session_id, update)


create_main_directory()
dict = {}
# Main loop of the program will run as long as server is up.
while True:
    # Accept new client.
    client_socket, client_address = server.accept()
    with client_socket, client_socket.makefile('rb') as client_file:
        # Receive client ID.
        client_id = client_file.readline().strip().decode()
        # receive session id from client - will be used only if client exists.
        client_session_id = client_file.readline().strip().decode()
        # verify received id - if exists push all folders to client, otherwise create new client and pull data.
        if verify_existing_client(client_id):
            # receive comment from client.
            comment = client_file.readline().strip().decode()
            # if comment is first connection from current session, push all data from client's folder to client.
            if comment == 'SYN_DATA':
                client_session_id = str(random.randint(1, sys.maxsize))
                # initialize new session.
                dict[(client_id, client_session_id)] = []
                utils.send_string(client_socket, client_session_id)
                # push directory to client.
                utils.push_data(client_socket, client_file, get_client_path(client_id))
            # otherwise client wants an update from the server.
            else:
                check_update(client_id, client_session_id, comment)
        # otherwise client is not an existing client.
        else:
            client_session_id = str(random.randint(1, sys.maxsize))
            # generate new id.
            client_id = generate_id()
            # initialize an empty dictionary for following client.
            dict[(client_id, client_session_id)] = []
            # print id.
            print(client_id)
            # send id to client.
            utils.send_string(client_socket, client_id)
            # send session id to client.
            utils.send_string(client_socket, client_session_id)
            # pull all data from given client.
            utils.pull_data(client_socket, client_file, get_client_path(client_id))
        # close client's socket.
        client_file.close()
