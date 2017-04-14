# using python2.7

"""
Server should the following in order:
    - server_port
    - block_duration
    - timeout
"""

import sys, threading
import datetime as time
from socket import socket, AF_INET, SOCK_STREAM
from socket import error as socket_error

# TODO find out how to get rid of global here
global SERVER_PORT, BLOCK_DURATION, TIMEOUT
credentials_filename = 'credentials.txt'
login_history = {}
users_online = {}

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


def serve_client(client_socket):
    while 1:
        message = client_socket.recv(1024)
        client_socket.send('#info Echo: ' + message)


def accept_client(client_socket):
    # prompt for credentials
    tries = 0
    accepted = False
    blocked = False
    send_prompt(client_socket, 'Username:')
    username = client_socket.recv(1024)
    while tries < 3:
        accepted, blocked = prompt_credentials(client_socket, username)
        if blocked:
            break
        if accepted:
            break
        else:
            if tries + 1 != 3:
                client_socket.send('#info Invalid Password. Please try again')
            tries += 1

    if blocked:
        client_socket.send('#terminate Your account is blocked due to multiple login failures. ' +
                              'Please try again later')
        client_socket.close()
    elif accepted:
        # add user to login history
        login_history[username] = time.datetime.now()
        client_socket.send('#accepted Welcome to the intergalactic chat service!')
        thread = threading.Thread(target=serve_client, args=(client_socket,))
        thread.daemon = True
        thread.start()
    else:
        blocked_login_attempts[username] = time.datetime.now()
        client_socket.send('#terminate Invalid Password. Your account has been blocked. ' +
                              'Please try again later')
        client_socket.close()


def start_server():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    try:
        serverSocket.bind(('', SERVER_PORT))
        serverSocket.listen(1)
        print 'The intergalactic chat server is listening for connections'

        while 1:
            connectionSocket, addr = serverSocket.accept()
            try:
                accept_client(connectionSocket)
            except socket_error:
                if socket_error.errno == 32:  # broken pipe
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
        # only shut down main thread when the threads are finished
        while threading.active_count > 0:
            time.sleep(0.1)

