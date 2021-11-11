# Itay Etelis 209041474
# Ben Levi 318811304

import socket
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('192.168.129.128', 12345))

s.send(b'Ben levi')
data = s.recv(100)
print("Server sent: ", data)

s.send(b'318811304')
data = s.recv(100)
print("Server sent: ", data)


s.close()
