# Itay Etelis 209041474
# Ben Levi 318811304

import socket
import sys
import os
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('192.168.129.128', 12345))
PATH = os.path.abspath(os.getcwd()) + '/check'
s.send(int.to_bytes(0, 4, 'little'))
time.sleep(1)

s.send(int.to_bytes(2, 4, 'little'))
time.sleep(1)

s.send('/c'.encode('utf8'))
time.sleep(1)

file = open(PATH + '/c', "rb")
s.send(int.to_bytes(os.path.getsize(PATH + '/c'), 4, 'little'))
time.sleep(1)

file_data = file.read(1024)
while file_data:
    s.send(file_data)
    file_data = file.read(1024)
file.close()


s.close()
