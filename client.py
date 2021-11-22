# Itay Etelis 209041474
# Ben Levi 318811304

import socket
import sys
import os
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import utils

IP = sys.argv[1]
PORT = int(sys.argv[2])
PATH = str(sys.argv[3])
TIME = float(sys.argv[4])
IN_PROGRESS = False
SEP = os.path.sep


class Client:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((IP, PORT))
        self.client_file = self.s.makefile('rb')
        self.id = '0'
        self.index = '0'
        self.start = time.time()

    def initialize_connection(self):
        try:
            self.id = str(sys.argv[5])
            utils.send_int(self.s, self.id)
            utils.send_string(self.s, 'SYN_DATA')
            self.index = self.client_file.readline().strip().decode()
            utils.pull_data(self.client_file, PATH)

        except:
            utils.send_string(self.s, self.id)
            self.id = self.client_file.readline().strip().decode()
            self.index = self.client_file.readline().strip().decode()
            utils.push_data(self.s, PATH)
            self.s.close()
        self.start = time.time()

    def socket_close(self):
        global IN_PROGRESS
        self.s.close()
        self.client_file.close()
        IN_PROGRESS = False

    def get_id(self):
        return self.id

    def socket_rst(self):
        global IN_PROGRESS
        if IN_PROGRESS:
            print("tried to enter while other socket is on")
        IN_PROGRESS = True
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((IP, PORT))
        self.client_file = self.s.makefile('rb')

    def get_updates(self):
        utils.send_string(self.s, self.id)
        utils.send_string(self.s, self.index)
        utils.send_string(self.s, 'UPDATE_TIME')
        print('sent UPDATE_TIME')
        num_updates = int((self.client_file.readline().decode().strip()))
        print('number of updates received:    ' + str(num_updates))
        for update in range(num_updates):
            comment = self.client_file.readline().decode().strip()
            print('Comment received =   ' + comment)
            if comment == 'NEW_FILE':
                utils.pull_new_file(self.client_file, PATH)

            elif comment == 'NEW_DIR':
                relative_path = self.client_file.readline().strip().decode()
                os.makedirs(utils.join_path_relativepath(relative_path, PATH), exist_ok=True)

            elif comment == 'DELETE':
                utils.pull_delete_file(self.client_file, PATH)
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
                global IN_PROGRESS
                if self.client.start + TIME < time.time() and not IN_PROGRESS:

                    print('START UPDATE')
                    self.client.socket_rst()
                    IN_PROGRESS = True
                    self.client.get_updates()
                    IN_PROGRESS = False
                    self.client.socket_close()
                    print('END UPDATE')
                time.sleep(5)
        except KeyboardInterrupt:
            self.my_observer.stop()
        self.my_observer.join()


class Handler(FileSystemEventHandler):
    def __init__(self, client):
        self.client = client

    def send_created_file(self, src_path):
        utils.send_string(self.client.s, self.client.id)
        utils.send_string(self.client.s, self.client.index)
        relative_path = str(src_path)[len(PATH):]
        if os.path.isdir(src_path):
            utils.send_string(self.client.s, 'NEW_DIR')
            utils.send_string(self.client.s, relative_path)
        else:
            utils.send_string(self.client.s, 'NEW_FILE')
            utils.send_created_file(self.client.s, src_path, PATH)


    def delete_file(self, src_path):
        utils.send_string(self.client.s, self.client.id)
        utils.send_string(self.client.s, self.client.index)
        relative_path = str(src_path)[len(PATH):]
        utils.send_string(self.client.s, 'DELETE')
        utils.send_string(self.client.s, relative_path)

    def on_any_event(self, event):
        global IN_PROGRESS
        if IN_PROGRESS:
            time.sleep(3)
            return
        if ((str(event.src_path).split(SEP))[-1])[0] == '.':
            if event.event_type != 'moved':
                return

        print('IN_PROCESS    ')
        print(IN_PROGRESS)
        self.client.socket_rst()
        if event.event_type == 'created':
            print(f"{event.src_path} has been created!")
            self.send_created_file(event.src_path)

        elif event.event_type == 'deleted':
            print(f"Someone deleted {event.src_path}!")
            self.delete_file(event.src_path)

        elif event.event_type == 'moved':
            if ((str(event.src_path).split(SEP))[-1])[0] == '.':
                print(f"someone modified {event.dest_path}")
                # problem if come new client between close to rst.
                self.delete_file(event.dest_path)
                self.client.socket_close()
                self.client.socket_rst()
                self.send_created_file(event.dest_path)
            else:
                print(f"someone moved {event.src_path} to {event.dest_path}")
                # problem if come new client between close to rst.
                self.delete_file(event.src_path)
                self.client.socket_close()
                self.client.socket_rst()
                self.send_created_file(event.dest_path)

        self.client.socket_close()


c = Client()
c.initialize_connection()
w = Watcher(c)
w.run()
