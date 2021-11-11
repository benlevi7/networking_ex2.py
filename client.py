# Itay Etelis 209041474
# Ben Levi 318811304

import socket
import sys
import os
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('192.168.129.128', 12345))
PATH = os.path.abspath(os.getcwd()) + '/check'

s.send('KCgeBzEKzY8045PfVRwC0aphrfwmZAfabFZEh5DVS5kGfVZwAoOobOnhksQo4zIOyrfKps2Ku1VtM12pNzGug11DD3bwYsJemLsDONvWdgE62GrGK8E1o9FTC8P0t0Pl'.encode('utf8'))

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


s.close()
