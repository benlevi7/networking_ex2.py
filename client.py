# Itay Etelis 209041474
# Ben Levi 318811304

import socket
import sys
import os
import time
import utils
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
        self.start = time.time()

    def initialize_connection(self):
        try:
            self.id = str(sys.argv[5])
            utils.send_int(self.s, self.id)
            utils.send_string(self.s, 'SYN_DATA')
            utils.pull_data(self.client_file, PATH)

        except:
            utils.send_string(self.s, self.id)
            self.id = self.client_file.readline().strip().decode()
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
        time.sleep(1)
        utils.send_string(self.s, 'UPDATE_TIME')
        time.sleep(1)
        update_time = (self.client_file.readline().decode().strip())
        if update_time > str(self.start):
            utils.send_string(self.s, 'PULL_ALL')
            time.sleep(1)
            for root, dirs, files in os.walk(PATH, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            utils.pull_data(self.client_file, PATH)
        else:
            utils.send_string(self.s, 'CONTINUE')
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
                if self.client.start + TIME < time.time() and not IN_PROGRESS:
                    self.client.socket_rst()
                    self.client.get_updates()
                    self.client.socket_close()
                time.sleep(5)
        except KeyboardInterrupt:
            self.my_observer.stop()
        self.my_observer.join()


class Handler(FileSystemEventHandler):
    def __init__(self, client):
        self.client = client

    def send_created_file(self, src_path):
        utils.send_string(self.client.s, self.client.id)
        time.sleep(1)
        relative_path = str(src_path)[len(PATH):]
        if os.path.isdir(src_path):
            utils.send_string(self.client.s, 'NEW_DIR')
            time.sleep(1)
            utils.send_string(self.client.s, relative_path)
            time.sleep(1)
        else:
            utils.send_string(self.client.s, 'NEW_FILE')
            time.sleep(1)
            utils.send_string(self.client.s, relative_path)
            time.sleep(1)
            utils.send_int(self.client.s, os.path.getsize(src_path))
            time.sleep(1)
            with open(str(src_path), 'rb') as f:
                self.client.s.sendall(f.read())


    def delete_file(self, src_path):
        utils.send_string(self.client.s, self.client.id)
        time.sleep(1)
        relative_path = str(src_path)[len(PATH):]
        utils.send_string(self.client.s, 'DELETE')
        time.sleep(1)
        utils.send_string(self.client.s, relative_path)
        time.sleep(1)

    def on_any_event(self, event):
        if IN_PROGRESS:
            return
        if ((str(event.src_path).split(SEP))[-1])[0] == '.':
            if event.event_type != 'moved':
                return
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

        self.client.start = time.time()
        self.client.socket_close()


c = Client()
c.initialize_connection()
w = Watcher(c)
w.run()
