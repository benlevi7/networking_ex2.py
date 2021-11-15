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


class Client:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((IP, PORT))
        self.id = '0'
        self.start = time.time()

    def initialize_connection(self):
        try:
            self.id = str(sys.argv[5])
            self.s.send(self.id.encode('utf8'))
            time.sleep(1)
            self.s.send(b'SYN_DATA')
            time.sleep(1)
            self.pull_data()

        except:
            self.s.send(self.id.encode('utf8'))
            time.sleep(1)
            self.id = self.s.recv(1024).decode('utf8')
            self.push_data()
        self.start = time.time()
        self.s.close()

    def socket_close(self):
        self.s.close()

    def get_id(self):
        return self.id

    def socket_rst(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((IP, PORT))

    def push_data(self):
        list_of_empty_dirs = list()
        for (dirpath, dirnames, filenames) in os.walk(PATH):
            if len(dirnames) == 0 and len(filenames) == 0:
                list_of_empty_dirs.append(dirpath[len(PATH):])

        num_files = sum(len(files) for _, _, files in os.walk(PATH))

        self.s.send(int.to_bytes(num_files, 4, 'little'))
        time.sleep(1)
        for root, dirs, files in os.walk(PATH):
            for name in files:
                relative_path = os.path.join(root[len(PATH) - 1:], name)
                self.s.send(relative_path.encode())
                time.sleep(0.5)
                self.s.send(int.to_bytes(os.path.getsize(PATH + relative_path), 4, 'little'))
                time.sleep(0.5)
                print(PATH + '/' + relative_path)
                file = open(PATH + relative_path, "rb")
                file_data = file.read(1024)
                while file_data:
                    self.s.send(file_data)
                    file_data = file.read(1024)
                file.close()

        time.sleep(1)
        self.s.send(int.to_bytes(len(list_of_empty_dirs), 4, 'little'))
        time.sleep(1)
        for empty_dir in list_of_empty_dirs:
            self.s.send(str(empty_dir).encode())
            time.sleep(1)

    # per request create requested file.
    def pull_new_file(self):
        relative_path = self.s.recv(1024).decode('utf-8')
        file_name = relative_path.split('/')[-1]
        relative_path = relative_path[0:relative_path.find(file_name)]

        if not os.path.exists(PATH + relative_path):
            os.makedirs(PATH + relative_path)

        file = open(PATH + relative_path + file_name, "wb")
        file_size = int.from_bytes(self.s.recv(1024), 'little')
        temp_size = 0

        while temp_size < file_size:
            byte_stream = self.s.recv(1024)
            temp_size += len(byte_stream)
            file.write(byte_stream)
        file.close()

    def pull_data(self):
        # get number of files expected to be received.
        numFiles = int.from_bytes(self.s.recv(1024), 'little')
        # iterate over all files and write them to folder.
        for indexFile in range(numFiles):
            # receive each file.
            self.pull_new_file()

        num_empty_dirs = int.from_bytes(self.s.recv(1024), 'little')
        for i in range(num_empty_dirs):
            os.makedirs(PATH + self.s.recv(1024).decode('utf-8'))

    def get_updates(self):
        self.s.send(self.id.encode('utf8'))
        time.sleep(1)
        self.s.send(b'UPDATE_TIME')
        time.sleep(1)
        update_time = self.s.recv(1024).decode('utf8')
        if update_time > str(self.start):
            self.s.send(b'PULL_ALL')
            time.sleep(1)
            for root, dirs, files in os.walk(PATH, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            self.pull_data()
        else:
            self.s.send(b'CONTINUE')
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
        self.client.s.send(self.client.get_id().encode('utf-8'))
        time.sleep(1)
        relative_path = str(src_path)[len(PATH):]
        if os.path.isdir(src_path):
            self.client.s.send(b'NEW_DIR')
            time.sleep(1)
            self.client.s.send(relative_path.encode('utf-8'))
            time.sleep(1)
        else:
            file = open(str(src_path), "rb")
            self.client.s.send(b'NEW_FILE')
            time.sleep(1)
            self.client.s.send(relative_path.encode('utf-8'))
            time.sleep(1)
            self.client.s.send(int.to_bytes(os.path.getsize(src_path), 4, 'little'))
            time.sleep(1)
            file_data = file.read(1024)
            while file_data:
                self.client.s.send(file_data)
                file_data = file.read(1024)
            file.close()


    def delete_file(self, src_path):
        self.client.s.send(self.client.get_id().encode('utf-8'))
        time.sleep(1)
        relative_path = str(src_path)[len(PATH):]
        print(src_path)
        if os.path.isdir(src_path):
            self.client.s.send(b'DELETE_DIR')
            time.sleep(1)
        else:
            print('delete_dir')
            self.client.s.send(b'DELETE_FILE')
            time.sleep(1)
        self.client.s.send(relative_path.encode('utf-8'))


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
