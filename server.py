# using python2.7

"""
Server should the following in order:
    - server_port
    - block_duration
    - timeout
"""

import sys
from socket import *

global SERVER_PORT, BLOCK_DURATION, TIMEOUT
login_history = {}
credentials_filename = 'credentials.txt'


def start_server():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', SERVER_PORT))
    serverSocket.listen(1)
    print 'The intergalactic chat server is ready to receive'
    while 1:
        connectionSocket, addr = serverSocket.accept()

        # prompt for credentials
        connectionSocket.send('#prompt Username:')
        username = connectionSocket.recv(1024)
        connectionSocket.send('#prompt Password:')
        password = connectionSocket.recv(1024)

        # check credentials

        connectionSocket.send('%s' % (username + ' ' + password))
        connectionSocket.close()

if __name__ == '__main__':
    cmdArgs = sys.argv
    if len(cmdArgs) != 4:
        print 'Usage: python server.py <server_port> <block_duration> <timeout>'
    else:
        # set variables
        global SERVER_PORT, BLOCK_DURATION, TIMEOUT
        SERVER_PORT = int(cmdArgs[1])
        BLOCK_DURATION = cmdArgs[2]
        TIMEOUT = cmdArgs[3]
        start_server()







