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


credentials_filename = 'credentials.txt'
login_history = {} # dictionary of login history and sockets: {'yoda': {'time': time, 'socket' socket}
users_online = [] # list of users ie ['yoda', 'luke']

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
        if time_elapsed.seconds > BLOCK_DURATION:
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
        if message == '':
            client_socket.close()
            break

        if message == 'logout':
            client_socket.send('#terminate client logs out')
            client_socket.close()
            break
        else:
            client_socket.send('#info Echo: ' + message)


def accept_client(client_socket):
    global login_history, users_online
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
        user_entry = {'time': time.datetime.now(), 'socket': client_socket}
        login_history[username] = user_entry
        client_socket.send('#accepted Welcome to the intergalactic chat service!')
        thread = threading.Thread(target=serve_client, args=(client_socket,))
        thread.daemon = True
        thread.start()

        # add to list of online users
        users_online.append(username)
    else:
        blocked_login_attempts[username] = time.datetime.now()
        client_socket.send('#terminate Invalid Password. Your account has been blocked. ' +
                              'Please try again later')
        client_socket.close()


def start_server():
    # dispatch thread to check active users
    timeout_thread = threading.Thread(target=check_timeouts)
    timeout_thread.daemon = True
    timeout_thread.start()

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


def check_timeouts():
    global users_online
    while 1:
        for user in users_online:
            time_at_login = login_history[user]['time']
            time_now = time.datetime.now()
            time_elapsed = time_now - time_at_login

            if time_elapsed.seconds > TIMEOUT:
                # close connection to timed out user
                user_sock = login_history[user]['socket']
                user_sock.send('#terminate timeout')
                user_sock.close()

                users_online.remove(user)


if __name__ == '__main__':
    cmdArgs = sys.argv
    if len(cmdArgs) != 4:
        print 'Usage: python server.py <server_port> <block_duration> <timeout>'
    else:
        # set variables
        SERVER_PORT = int(cmdArgs[1])
        BLOCK_DURATION = cmdArgs[2]
        TIMEOUT = int(cmdArgs[3])
        start_server()
