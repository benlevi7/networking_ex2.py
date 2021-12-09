# Itay Etelis 209041474
# Ben Levi 318811304

import os
import time

SEP = os.path.sep


# send_string - basic usage of makefile to send strings over TCP.
#    @param sock - the socket used to send the message over TCP.
#    @param string - given string to send over TCP.
def send_string(sock,string):
    sock.sendall(string.encode() + b'\n')


# send_int - basic usage of makefile to send ints over TCP.
    # @param sock - the socket used to send the message over TCP.
    # @param int - given int to send over TCP.
def send_int(sock, integer):
    sock.sendall(str(integer).encode() + b'\n')


# replace_separators - will replace separators according to system.
    # @param path - the path for the operation.
    # return - returns fixed path with correct separators.
def replace_separators(path):
    if SEP == '/':
        return str(path).replace('\\', SEP)
    return str(path).replace('/', SEP)


# join_paths - will join both relative path and general path with correct separators.
    # @param relative_path - relative path provided.
    # @param folder_path - main folder path provided.
    # return - returns fixed folder + relative path path for future use.
def join_paths(relative_path, folder_path):
    # if relative path does not start with a separator, insert one.
    if not str(relative_path).startswith('/') and not str(relative_path).startswith('\\'):
        relative_path = ''.join(SEP + replace_separators(relative_path))
    # if folder's path ends with separator remove it.
    if str(folder_path).endswith(SEP):
        folder_path = folder_path[:-1]

    # return product.
    return folder_path + relative_path


# pull_data - will be used to pull all data into path folder.
    # @param client_socket - the socket used to send the message over TCP.
    # @param client_file - makefile object of the given socket.
    # @param path - destination for pull request.
    # return - returns the relative path received for future use.
def pull_data(client_socket, client_file, path):
    # get number of files expected to be received.
    num_files = int(client_file.readline())
    # iterate over all files and write them to folder.
    for indexFile in range(num_files):
        # receive each file.
        pull_new_file(client_socket, client_file, path)

    # receive number of empty directories expected.
    num_empty_dirs = int(client_file.readline())
    # iterate over empty folders and receive them.
    for i in range(num_empty_dirs):
        os.makedirs(join_paths(client_file.readline().strip().decode(), path), exist_ok=True)


# pull_new_file - per request create requested file.
    # @param client_socket - the socket used to send the message over TCP.
    # @param client_file - makefile object of the given socket.
    # @param path - destination for pull request.
    # return - returns the relative path received for future use.
def pull_new_file(client_socket, client_file, path):
    # receive relative path from client and create a path with corresponding separator.
    relative_path = replace_separators(client_file.readline().strip().decode())

    # separate file's name from path.
    file_name = relative_path.split(SEP)[-1]
    relative_path_no_name = relative_path[0:relative_path.find(file_name)]

    folder_path = join_paths(relative_path_no_name, path)
    # if folder does not exists create new folder.
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)

    # receive expected file's size.
    file_size = int(client_file.readline())
    # read incoming packages until all file has been received.
    byte_stream = client_file.read(file_size)
    # created file in path.
    with open((join_paths(file_name, folder_path)), 'wb') as f:
        f.write(byte_stream)
    return relative_path


# push_data - per request push all data inside the path folder.
    # @param socket - the socket used to send the message over TCP.
    # @param client_file - makefile object of the given socket.
    # @param path - destination for pull request.
def push_data(socket, client_file, path):
    # find all empty dirs and store them in a designated list.
    list_of_empty_dirs = list()
    for (dirpath, dirnames, filenames) in os.walk(path):
        if len(dirnames) == 0 and len(filenames) == 0:
            list_of_empty_dirs.append(dirpath[len(path):])
    # send number of files expected to be sent.
    num_files = sum(len(files) for _, _, files in os.walk(path))
    send_int(socket, num_files)

    # iterate over the files inside the directory and send them.
    for root, dirs, files in os.walk(path):
        for name in files:
            relative_path = join_paths(name, root)
            push_file(socket, client_file, relative_path, path)
    # send number of empty directories expected to be sent.
    send_int(socket, len(list_of_empty_dirs))
    # send each dir's name.
    for empty_dir in list_of_empty_dirs:
        send_string(socket, empty_dir)


# push_file - receives file to be sent and sends it.
    # @param client_socket - the socket used to send the message over TCP.
    # @param client_file - makefile object of the given socket.
    # @param src_path - location of the desired file.
def push_file(client_socket, client_file, src_path, path):
    # eject relative path from given src_path.
    relative_path = str(src_path)[len(path):]
    send_string(client_socket, relative_path)
    # send expected file's size.
    file_size = os.path.getsize(src_path)
    send_int(client_socket, file_size)
    # open the desired file and sent it.
    #######################
    open_file(client_socket, src_path)


def open_file(client_socket, src_path):
    try:
        with open(str(src_path), 'rb') as f:
            content = f.read()
            client_socket.sendall(content)
    except:
        time.sleep(1)
        open_file(client_socket, src_path)


# pull_delete_file - per request delete requested file.
    # @param client_file - makefile object of the given socket.
    # @param path - main folder's path.
    # return - returns the relative path received for future use.
def pull_delete_file(client_file, path):
    # receive relative path.
    relative_path = replace_separators(client_file.readline().strip().decode())
    # join relative path with folder's path.
    full_path = join_paths(relative_path, path)
    # if files exists, check if is actually a folder, if so create a folder otherwise delete the file.
    if os.path.exists(full_path):
        if os.path.isdir(full_path):
            # make sure the folder is actually empty.
            delete_not_empty_dir(full_path)
        else:
            os.remove(full_path)
    return relative_path


# delete_not_empty_dir - make sure given folder is empty before deleting it.
    # @param path - main folder's path.
def delete_not_empty_dir(path):
    # iterate over the folder and remove all files and folder's inside accordingly.
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(path)
