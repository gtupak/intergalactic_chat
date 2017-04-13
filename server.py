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
credentials_filename = 'credentials.txt'
login_history = {}

# load credentials
creds_file = open(credentials_filename, 'r')
creds_lines = creds_file.readlines()
creds_lines = [line.translate(None, '\n') for line in creds_lines] # remove \n characters from credentials


def prompt_credentials(sock):
    accepted = False

    sock.send('#prompt Username:')
    username = sock.recv(1024)
    sock.send('#prompt Password:')
    password = sock.recv(1024)

    # check credentials
    creds = '%s %s' % (username, password)
    if creds in creds_lines:
        accepted = True

    return accepted


def start_server():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', SERVER_PORT))
    serverSocket.listen(1)
    print 'The intergalactic chat server is listening for connections'

    while 1:
        connectionSocket, addr = serverSocket.accept()

        # prompt for credentials
        tries = 0
        accepted = False
        while tries < 3:
            accepted = prompt_credentials(connectionSocket)
            if accepted:
                break
            else:
                if tries + 1 != 3:
                    connectionSocket.send('#info Invalid Password. Please try again')
                tries += 1

        if accepted:
            connectionSocket.send('Welcome to the intergalactic chat service!')
            connectionSocket.close()
        else:
            connectionSocket.send('Invalid Password. Your account has been blocked. Please try again later')
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







