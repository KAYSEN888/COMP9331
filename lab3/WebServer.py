# COMP9331 - LAB 3
# Luo Kaisen
# z5185842

from socket import *
import sys

serverPort = int(sys.argv[1])
serverName = '127.0.0.1'
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((serverName, serverPort))
serverSocket.listen(1)

while True:
    connectionSocket, addr = serverSocket.accept()
    try:
        message = connectionSocket.recv(1024).decode()
        if not message:
            continue
        # get the file name
        file = message.split()[1]
        f = open(file[1:], 'rb')
        output = f.read()
        header = 'HTTP/1.1 200 OK\r\n\r\n'
        connectionSocket.send(header.encode())
        connectionSocket.sendall(output)
        connectionSocket.close()

    except IOError:
        header = 'HTTP/1.1 404 NOT FOUND\r\n\r\n'
        error = '404 NOT FOUND'
        connectionSocket.send(header.encode())
        connectionSocket.send(error.encode())
        connectionSocket.close()

serverSocket.close()
