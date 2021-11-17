import os


def send_string(sock,string):
    sock.sendall(string.encode() + b'\n')


def send_int(sock,integer):
    sock.sendall(str(integer).encode() + b'\n')


def pull_data(client_file, path):
    # get number of files expected to be received.
    num_files = int(client_file.readline())
    # iterate over all files and write them to folder.
    for indexFile in range(num_files):
        # receive each file.
        pull_new_file()

    num_empty_dirs = int(client_file.readline())
    for i in range(num_empty_dirs):
        os.makedirs(path + client_file.readline().strip().decode(), exist_ok=True)


    # per request create requested file.
def pull_new_file(client_file, path):
    relative_path = client_file.readline().strip().decode()
    file_name = relative_path.split('/')[-1]
    relative_path = relative_path[0:relative_path.find(file_name)]

    if not os.path.exists(path + relative_path):
        os.makedirs((path + relative_path), exist_ok=True)

    file_size = int(client_file.readline())
    byte_stream = client_file.read(file_size)
    with open((path + relative_path + file_name), 'wb') as f:
        f.write(byte_stream)


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
            relative_path = root[len(path):] + '/' + name
            if relative_path[0] == '/':
                relative_path = relative_path[1:]
            send_string(socket, relative_path)
            send_int(socket, os.path.getsize(path + relative_path))
            with open((path + relative_path), 'rb') as f:
                socket.sendall(f.read())

    send_int(socket, len(list_of_empty_dirs))
    for empty_dir in list_of_empty_dirs:
        send_string(socket, empty_dir)
