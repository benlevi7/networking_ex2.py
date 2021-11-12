# Itay Etelis 209041474
# Ben Levi 318811304

import socket
import sys
import os
import time
import watchdog
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

"""
IP = sys.argv[1]
PORT = sys.argv[2]
PATH = sys.argv[3]
TIME = sys.argv[4]
if len(sys.argv) == 6:
    ID = sys.argv[5]
else:
    ID = 0

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((IP, PORT))

def pushData():
    numFiles = sum(len(files) for _, _, files in os.walk(PATH))
    s.send(int.to_bytes(numFiles, 4, 'little'))
    time.sleep(1)
    for root, dirs, files in os.walk(PATH):
        for name in files:
            relativePath = os.path.join(root[len(PATH):], name)
            s.send(relativePath.encode('utf8'))
            time.sleep(1)
            s.send(int.to_bytes(os.path.getsize(PATH + '/' + relativePath), 4, 'little'))
            time.sleep(1)
            file = open(PATH + '/' + relativePath, "rb")
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
if ID == 0:
    pushData()
else:
    pullData()

"""

PATH = "/home/benle/PycharmProjects/networking_ex2.py/check"

patterns = ["*"]
ignore_patterns = None
ignore_directories = False
case_sensitive = True
my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)

def on_created(event):
     print(f"{event.src_path} has been created!")

def on_deleted(event):
     print(f"Someone deleted {event.src_path}!")


def on_moved(event):
    print(f"someone moved {event.src_path} to {event.dest_path}")


my_event_handler.on_created = on_created
my_event_handler.on_deleted = on_deleted
my_event_handler.on_moved = on_moved

path = PATH
go_recursively = True
my_observer = Observer()
my_observer.schedule(my_event_handler, path, recursive=go_recursively)

my_observer.start()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    my_observer.stop()
    my_observer.join()


#s.close()
