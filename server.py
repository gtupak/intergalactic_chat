# using python2.7

"""
Server should the following in order:
    - server_port
    - block_duration
    - timeout
"""

import sys
import datetime as time
from socket import *

# TODO find out how to get rid of global here
global SERVER_PORT, BLOCK_DURATION, TIMEOUT
credentials_filename = 'credentials.txt'
login_history = {}
# dictionary storing usernames of people blocked due of incorrect passwords
# stored as 'username': 'date_when_blocked'
blocked_login_attempts = {}

# load credentials
creds_file = open(credentials_filename, 'r')
creds_lines = creds_file.readlines()
creds_lines = [line.translate(None, '\n') for line in creds_lines] # remove \n characters from credentials


def prompt_credentials(sock, username):
    accepted = False
    blocked = False

    sock.send('#prompt Password:')
    password = sock.recv(1024)

    # check if blocked
    if username in blocked_login_attempts:
        time_now = time.datetime.now()
        time_elapsed = time_now - blocked_login_attempts[username]
        if time_elapsed.seconds > TIMEOUT:
            del blocked_login_attempts[username]
        else:
            blocked = True

    # check credentials
    if not blocked:
        creds = '%s %s' % (username, password)
        if creds in creds_lines:
            accepted = True

    return accepted, blocked

def send_prompt(sock, msg):
    sock.send('#prompt %s' % msg)
    return

def start_server():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    try:
        serverSocket.bind(('', SERVER_PORT))
        serverSocket.listen(1)
        print 'The intergalactic chat server is listening for connections'

        while 1:
            connectionSocket, addr = serverSocket.accept()

            # prompt for credentials
            tries = 0
            accepted = False
            blocked = False
            send_prompt(connectionSocket, 'Username:')
            username = connectionSocket.recv(1024)
            while tries < 3:
                accepted, blocked = prompt_credentials(connectionSocket, username)
                if blocked:
                    break
                if accepted:
                    break
                else:
                    if tries + 1 != 3:
                        connectionSocket.send('#info Invalid Password. Please try again')
                    tries += 1

            if blocked:
                connectionSocket.send('#terminate Your account is blocked due to multiple login failures. ' +
                                      'Please try again later')
                connectionSocket.close()
            elif accepted:
                connectionSocket.send('Welcome to the intergalactic chat service!')
                connectionSocket.close()
            else:
                blocked_login_attempts[username] = time.datetime.now()
                connectionSocket.send('#terminate Invalid Password. Your account has been blocked. Please try again later')
                connectionSocket.close()
    except KeyboardInterrupt:
        print 'Intergalactic chat server is shutting down gracefully'
        serverSocket.close()

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

