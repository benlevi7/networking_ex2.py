import os
import time

SEP = os.path.sep

def send_string(sock,string):
    sock.sendall(string.encode() + b'\n')


def send_int(sock, integer):
    sock.sendall(str(integer).encode() + b'\n')


def pull_data(client_file, path):
    # get number of files expected to be received.
    num_files = int(client_file.readline())
    print('number of files sent from client: ' + str(num_files))
    # iterate over all files and write them to folder.
    for indexFile in range(num_files):
        # receive each file.
        pull_new_file(client_file, path)

    num_empty_dirs = int(client_file.readline())
    for i in range(num_empty_dirs):
        os.makedirs(join_path_relativepath(client_file.readline().strip().decode(), path), exist_ok=True)


# per request create requested file.
def pull_new_file(client_file, path):
    relative_path = replace_seperators(client_file.readline().strip().decode())
    print('relative path sent from client' + relative_path)
    file_name = relative_path.split(SEP)[-1]
    relative_path_no_name = relative_path[0:relative_path.find(file_name)]

    folder_path = join_path_relativepath(relative_path_no_name, path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)

    file_size = int(client_file.readline())
    print('files size' + str(file_size))
    byte_stream = client_file.read(file_size)
    with open((join_path_relativepath(file_name, folder_path)), 'wb') as f:
        f.write(byte_stream)
    return relative_path


def push_data(socket, path):
    list_of_empty_dirs = list()
    for (dirpath, dirnames, filenames) in os.walk(path):
        if len(dirnames) == 0 and len(filenames) == 0:
            list_of_empty_dirs.append(dirpath[len(path):])

    num_files = sum(len(files) for _, _, files in os.walk(path))

    send_int(socket, num_files)
    for root, dirs, files in os.walk(path):
        for name in files:
            print(root)
            relative_path = join_path_relativepath(name, root[len(path):])
            send_string(socket, relative_path)
            send_int(socket, os.path.getsize(path + relative_path))
            with open((path + relative_path), 'rb') as f:
                socket.sendall(f.read())

    send_int(socket, len(list_of_empty_dirs))
    for empty_dir in list_of_empty_dirs:
        send_string(socket, empty_dir)


def replace_seperators(path):
    if SEP == '/':
        return str(path).replace('\'', SEP)
    return str(path).replace('/', SEP)


def join_path_relativepath(relative_path, folder_path):
    if not str(relative_path).startswith('/') and not str(relative_path).startswith('\''):
        relative_path = ''.join(SEP + replace_seperators(relative_path))
    folder_path = str(folder_path).removesuffix(SEP)
    return folder_path + relative_path


def send_created_file(client_socket, src_path, path):
    relative_path = str(src_path)[len(path):]
    send_string(client_socket, relative_path)
    send_int(client_socket, os.path.getsize(src_path))
    with open(str(src_path), 'rb') as f:
        client_socket.sendall(f.read())


# per request delete requested file.
def pull_delete_file(client_file, path):
    relative_path = client_file.readline().strip().decode()
    print(relative_path)
    full_path = join_path_relativepath(relative_path, path)
    print('full path' + full_path)
    if os.path.exists(full_path):
        if os.path.isdir(full_path):
            delete_not_empty_dir(full_path)
        else:
            os.remove(full_path)
    return relative_path

def delete_not_empty_dir(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(path)
