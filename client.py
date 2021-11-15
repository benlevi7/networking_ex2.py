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
PATH = sys.argv[3]
TIME = float(sys.argv[4])
try:
    ID = sys.argv[5]
    print(ID)
except:
    ID = '0'
    print(ID)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((IP, PORT))

###########################################################################################


class Watcher:
    def __init__(self, path):
        self.my_observer = Observer()
        self.path = path
        self.start = time.time()

    def run(self):
        my_event_handler = Handler()
        self.my_observer.schedule(my_event_handler, self.path, recursive=True)
        self.my_observer.start()
        try:
            global s
            while True:
                if self.start + TIME < time.time():
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((IP, PORT))
                    self.get_updates()
                    s.close()
                time.sleep(5)
        except KeyboardInterrupt:
            self.my_observer.stop()
        self.my_observer.join()

    def get_updates(self):
        s.send(ID.encode('utf8'))
        time.sleep(1)
        print(ID)
        s.send(b'UPDATE_TIME')
        update_time = s.recv(1024).decode('utf8')
        print(update_time)
        print(self.start)
        if update_time > str(self.start):
            s.send(b'PULL_ALL')
            for root, dirs, files in os.walk(PATH, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

            pullData()
        else:
            s.send(b'CONTINUE')
        self.start = time.time()
        s.close()


###########################################################################################


def send_created_file(src_path):
    relativePath = str(src_path)[str(src_path).find(PATH) + len(PATH):len(str(src_path))]
    file = open(str(src_path), "rb")
    s.send(b'NEW_FILE')
    time.sleep(1)
    s.send(relativePath.encode('utf8'))
    time.sleep(1)
    s.send(int.to_bytes(os.path.getsize(src_path), 4, 'little'))
    time.sleep(1)
    file_data = file.read(1024)
    while file_data:
        s.send(file_data)
        file_data = file.read(1024)
    file.close()


def delete_file(src_path):
    relativePath = str(src_path)[str(src_path).find(PATH) + len(PATH):len(str(src_path))]
    print(relativePath)
    s.send(b'DELETE_FILE')
    time.sleep(1)
    s.send(relativePath.encode('utf8'))


class Handler(FileSystemEventHandler):

    def on_any_event(self, event):
        global s
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(1)
        if event.event_type == 'created':
            s.connect((IP, PORT))
            s.send(ID.encode('utf8'))
            print(f"{event.src_path} has been created!")
            send_created_file(event.src_path)

        elif event.event_type == 'deleted':
            s.connect((IP, PORT))
            s.send(ID.encode('utf8'))
            print(f"Someone deleted {event.src_path}!")
            delete_file(event.src_path)

        elif event.event_type == 'moved':
            s.connect((IP, PORT))
            s.send(ID.encode('utf8'))
            print(f"someone moved {event.src_path} to {event.dest_path}")
            delete_file(event.src_path)
            send_created_file(event.dest_path)
        s.close()


###########################################################################################


def pushData():
    numFiles = sum(len(files) for _, _, files in os.walk(PATH))
    s.send(int.to_bytes(numFiles, 4, 'little'))
    time.sleep(1)
    for root, dirs, files in os.walk(PATH):
        for name in files:
            relative_path = os.path.join(root[len(PATH):], name)
            print(relative_path)
            s.send(relative_path.encode('utf8'))
            time.sleep(1)
            s.send(int.to_bytes(os.path.getsize(PATH + '/' + relative_path), 4, 'little'))
            time.sleep(1)
            file = open(PATH + '/' + relative_path, "rb")
            print(PATH + '/' + relative_path, "rb")
            file_data = file.read(1024)
            while file_data:
                s.send(file_data)
                file_data = file.read(1024)
            file.close()


def pullData():
    numFiles = int.from_bytes(s.recv(1024), 'little')
    for indexFile in range(numFiles):
        relativePath = s.recv(1024).decode('utf8')
        fileName = relativePath.split('/')[-1]
        relativePath = relativePath[0:relativePath.find(fileName)]
        if not os.path.exists(PATH + relativePath):
            os.makedirs(PATH + relativePath)
        file = open(PATH + relativePath + '/' + fileName, "wb")
        fileSize = int.from_bytes(s.recv(1024), 'little')
        tempSize = 0
        while tempSize < fileSize:
            data = s.recv(1024)
            tempSize += len(data)
            file.write(data)
        file.close()


s.send(ID.encode('utf8'))
if ID == '0':
    ID = s.recv(1024).decode('utf8')
    pushData()
else:
    time.sleep(1)
    s.send(b'SYN_DATA')
    pullData()
s.close()

w = Watcher(PATH)
w.run()

