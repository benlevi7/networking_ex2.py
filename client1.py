# Itay Etelis 209041474
# Ben Levi 318811304

import socket
import sys
import os
import time
import watchdog
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

IP = sys.argv[1]
PORT = int(sys.argv[2])
PATH = str(sys.argv[3])
TIME = float(sys.argv[4])
PAUSED = False


def send_string(sock,string):
    sock.sendall(string.encode() + b'\n')


def send_int(sock,integer):
    sock.sendall(str(integer).encode() + b'\n')


class Client:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.s.connect((IP, PORT))

        self.clientfile = self.s.makefile('rb')

        self.id = '0'

        self.start = time.time()

    def initialize_connection(self):
        try:
            self.id = str(sys.argv[5])
            send_int(self.s, self.id)
            time.sleep(1)
            self.s.sendall(b'SYN_DATA')
            time.sleep(1)
            self.pull_data()

        except:
            send_string(self.s, self.id)
            time.sleep(1)
            self.id = self.clientfile.readline().strip().decode()
            self.push_data()

        self.start = time.time()
        self.s.close()

    def socket_close(self):
        self.s.close()
        self.clientfile.close()

    def get_id(self):
        return self.id

    def socket_rst(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((IP, PORT))
        self.clientfile = self.s.makefile('rb')

    def push_data(self):
        list_of_empty_dirs = list()
        for (dirpath, dirnames, filenames) in os.walk(PATH):
            if len(dirnames) == 0 and len(filenames) == 0:
                list_of_empty_dirs.append(dirpath[len(PATH):])

        num_files = sum(len(files) for _, _, files in os.walk(PATH))

        send_int(self.s, num_files)
        time.sleep(1)
        for root, dirs, files in os.walk(PATH):
            for name in files:
                print(root)
                relative_path = root[len(PATH):] + name
                print(relative_path)
                send_string(self.s, relative_path)
                time.sleep(0.5)
                send_int(self.s, os.path.getsize(PATH + relative_path))
                time.sleep(0.5)
                with open(os.path.join(PATH, relative_path), 'rb') as f:
                    self.s.sendall(f.read())


        time.sleep(1)
        send_int(self.s, len(list_of_empty_dirs))
        time.sleep(1)
        for empty_dir in list_of_empty_dirs:
            send_string(self.s, empty_dir)
            time.sleep(1)

    # per request create requested file.
    def pull_new_file(self):
        relative_path = self.clientfile.readline().strip().decode()
        file_name = relative_path.split('/')[-1]
        relative_path = relative_path[0:relative_path.find(file_name)]

        if not os.path.exists(PATH + relative_path):
            os.makedirs(os.path.join(PATH, relative_path))

        file_size = int(self.clientfile.readline())
        byte_stream = self.clientfile.read(file_size)
        with open(os.path.join(PATH, relative_path, file_name), 'wb') as f:
            f.write(byte_stream)

    def pull_data(self):
        # get number of files expected to be received.
        num_files = int(self.clientfile.readline())
        # iterate over all files and write them to folder.
        for indexFile in range(num_files):
            # receive each file.
            self.pull_new_file()

        num_empty_dirs = int(self.clientfile.readline())
        for i in range(num_empty_dirs):
            os.makedirs(os.path.join(PATH + self.clientfile.readline().strip().decode()))

    def get_updates(self):
        send_string(self.s, self.id)
        time.sleep(1)
        self.s.sendall(b'UPDATE_TIME')
        time.sleep(1)
        update_time = self.clientfile.readline().strip().decode()
        if update_time > str(self.start):
            self.s.sendall(b'PULL_ALL')
            time.sleep(1)
            for root, dirs, files in os.walk(PATH, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            self.pull_data()
        else:
            self.s.sendall(b'CONTINUE')
        self.start = time.time()


class Watcher:
    def __init__(self, client):
        self.my_observer = Observer()
        self.client = client

    def run(self):
        my_event_handler = Handler(self.client)
        self.my_observer.schedule(my_event_handler, PATH, recursive=True)
        self.my_observer.start()
        try:
            while True:
                global PAUSED
                if self.client.start + TIME < time.time():
                    PAUSED = True
                    self.client.socket_rst()
                    self.client.get_updates()
                    self.client.socket_close()
                    PAUSED = False
                time.sleep(5)
        except KeyboardInterrupt:
            self.my_observer.stop()
        self.my_observer.join()



class Handler(FileSystemEventHandler):
    def __init__(self, client):
        self.client = client


    def send_created_file(self, src_path):
        send_string(self.client.s, self.client.get_id())
        time.sleep(1)
        relative_path = str(src_path)[len(PATH):]
        if os.path.isdir(src_path):
            self.client.s.sendall(b'NEW_DIR')
            time.sleep(1)
            send_string(self.client.s, relative_path)
            time.sleep(1)
        else:
            self.client.s.sendall(b'NEW_FILE')
            time.sleep(1)
            send_string(self.client.s, relative_path)
            time.sleep(1)
            send_int(self.client.s, os.path.getsize(src_path))
            time.sleep(1)
            with open(str(src_path), 'rb') as f:
                self.client.s.sendall(f.read())

    def delete_file(self, src_path):
        send_string(self.client.s, self.client.get_id())
        time.sleep(1)
        relative_path = str(src_path)[len(PATH):]
        print(src_path)
        if os.path.isdir(src_path):
            self.client.s.sendall(b'DELETE_DIR')
            time.sleep(1)
        else:
            self.client.s.sendall(b'DELETE_FILE')
            time.sleep(1)
        send_string(self.client.s, relative_path)


    def on_any_event(self, event):
        if PAUSED:
            return
        self.client.socket_rst()
        if event.event_type == 'created':
            print(f"{event.src_path} has been created!")
            self.send_created_file(event.src_path)

        elif event.event_type == 'deleted':
            print(f"Someone deleted {event.src_path}!")
            self.delete_file(event.src_path)

        elif event.event_type == 'moved':
            print(f"someone moved {event.src_path} to {event.dest_path}")
            # problem if come new client between close to rst.
            self.delete_file(event.src_path)
            self.client.socket_close()
            self.client.socket_rst()
            self.send_created_file(event.dest_path)

        self.client.start = time.time()
        self.client.socket_close()


c = Client()
c.initialize_connection()
w = Watcher(c)
w.run()
