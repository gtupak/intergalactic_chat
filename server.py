# using python2.7

"""
Server should the following in order:
    - server_port
    - block_duration
    - timeout
"""

import sys, threading
import datetime as time
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from socket import error as socket_error


credentials_filename = 'credentials.txt'
login_history = {} # dictionary of login history sockets and user activity: {'yoda': {'time': time, 'socket' socket, 'lastActive': time}}
users_online = [] # list of users ie ['yoda', 'luke']

# dictionary storing usernames of people blocked due of incorrect passwords
# stored as 'username': 'date_when_blocked'
blocked_login_attempts = {}

blocked_IPs = {}

# load credentials
creds_file = open(credentials_filename, 'r')
creds_lines = creds_file.readlines()
creds_lines = [line.translate(None, '\n') for line in creds_lines] # remove \n characters from credentials

all_users = [line.split()[0] for line in creds_lines]

'''
Dictionary to store offline messages. Structured as follows:
{
    <user1>: [msg1, msg2, msg3],
    <user2>: [...]
}
'''
offline_msgs = {}

'''
Dictionary to store a blacklist. Structured as follows:
{
    <user1>: [blocked_user1, blocked_user2],
    <user2>: [...]
}
'''
blacklists = {}


def prompt_credentials(sock, username):
    accepted = False
    blocked = False

    send_prompt(sock, 'Password:')
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


def send_info(usr, msg):
    sock = login_history[usr]['socket']
    sock.send('#info %s' % msg)
    return


def send_direct_msg(usr_from, usr_to, msg):
    if usr_to in blacklists:
        blacklist = blacklists[usr_to]
        if usr_from in blacklist:
            send_info(usr_from, 'Your message could not be delivered as the recipient has blocked you.')
            return

    send_info(usr_to, '%s: %s' % (usr_from, msg))
    return


def broadcast(user_from, msg, login_logout_timeout):
    has_blocked_users = False
    for user in users_online:
        # do not broadcast to originated user
        if user == user_from:
            continue

        if user in blacklists:
            blacklist = blacklists[user]
            if user_from in blacklist:
                if not login_logout_timeout:
                    has_blocked_users = True
                continue

        send_info(user, '%s: %s' % (user_from, msg))

    if has_blocked_users:
        # make sure that user_from is still online (this could be a logout broadcast)
        if user_from in users_online:
            send_info(user_from, 'Your message could not be delivered to some recipients')

    return


def is_blocked_by(u_requester, u_query):
    if u_requester not in blacklists:
        return False

    users_blocked = blacklists[u_requester]
    if u_query in users_blocked:
        return True

    return False


def add_to_blacklist(requester, user_to_block):
    global blacklists

    if requester in blacklists:
        blacklist = blacklists[requester]
        if user_to_block not in blacklist:
            blacklist.append(user_to_block)
            blacklists[requester] = blacklist
    else:
        blacklist = [user_to_block]
        blacklists[requester] = blacklist
    return


def remove_from_blacklist(requester, user_to_unblock):
    global blacklists
    unblocked = False

    if requester in blacklists:
        blacklist = blacklists[requester]
        if user_to_unblock in blacklist:
            index = blacklist.index(user_to_unblock)
            del blacklist[index]
            blacklists[requester] = blacklist
            unblocked = True

    return unblocked


def serve_client(client_socket, user):
    global users_online, login_history

    while 1:

        message = client_socket.recv(1024)
        if message == '':
            client_socket.close()
            break

        # update user activity
        login_history[user]['lastActive'] = time.datetime.now()

        if message == 'logout':
            client_socket.send('#terminate client logs out')
            client_socket.close()
            users_online.remove(user)

            broadcast(user, '%s logged out' % user, True)
            break

        elif message == 'whoelse':
            for u_online in users_online:
                if user == u_online:
                    continue
                send_info(user, u_online)

        elif message.split()[0] == 'broadcast':
            message = ' '.join(message.split()[1:])
            broadcast(user, message, False)

        elif len(message.split()) > 2 and message.split()[0] == 'message':
            receiver = message.split()[1]
            if receiver not in all_users:
                send_info(user, 'User %s does not exist' % receiver)
                continue
            elif receiver == user:
                send_info(user, 'Cannot send message to self.')
                continue

            # check if receiver is online
            msg_to_send = ' '.join(message.split()[2:])
            if receiver in users_online:
                send_direct_msg(user, receiver, msg_to_send)
            else:
                if receiver in offline_msgs:
                    offline_msgs[receiver].append('%s: %s' % (user, msg_to_send))
                else:
                    offline_msgs[receiver] = ['%s: %s' % (user,msg_to_send)]

        elif len(message.split()) == 2 and message.split()[0] == 'block':
            # check if user to block exists
            user_to_block = message.split()[1]
            if user_to_block not in all_users:
                send_info(user, 'Username %s could not be found.' % user_to_block)
                continue

            elif user_to_block == user:
                send_info(user, 'Cannot block self.')
                continue

            add_to_blacklist(user, user_to_block)
            send_info(user, '%s is blocked.' % user_to_block)

        elif len(message.split()) == 2 and message.split()[0] == 'unblock':
            user_to_unblock = message.split()[1]
            if user_to_unblock not in all_users:
                send_info(user, '%s does not exist.')
                continue

            if user_to_unblock == user:
                send_info(user, 'Cannot unblock self.')
                continue

            unblocked = remove_from_blacklist(user, user_to_unblock)
            if unblocked:
                send_info(user, '%s has been unblocked.' % user_to_unblock)
            else:
                send_info(user, '%s user was not blocked.' % user_to_unblock)

        elif len(message.split()) == 2 and message.split()[0] == 'whoelsesince':
            try:
                now = time.datetime.now()
                timeSince = int(message.split()[1])
                historyOfUsers = []
                for login in login_history.keys():
                    if login == user:
                        continue

                    loginTime = login_history[login]['time']
                    interval = now - loginTime
                    if interval.seconds <= timeSince:
                        historyOfUsers.append(login)

                send_info(user, 'Users logged in since %d seconds: %s' % (timeSince, ' '.join(historyOfUsers)))
            except ValueError:
                send_info(user, 'Bad command. Time has be to be an integer.')

        else:
            client_socket.send('#info Echo: ' + message) # TODO to delete


def accept_client(client_socket):
    global login_history, users_online
    tries = 0
    accepted = False
    blocked = False

    # check if IP is blocked
    if client_socket.getpeername()[0] in blocked_IPs:
        now = time.datetime.now()
        timeAtBlock = blocked_IPs[client_socket.getpeername()[0]]
        interval = now - timeAtBlock
        if interval.seconds > BLOCK_DURATION:
            del blocked_IPs[client_socket.getpeername()[0]]
        else:
            client_socket.send('#terminate Your IP has been blocked for entering an invalid username. Try again later')
            client_socket.close()
            return

    # prompt for credentials
    send_prompt(client_socket, 'Username:')
    username = client_socket.recv(1024)

    if username in users_online:
        client_socket.send('#terminate Access denied. User is already logged in.')
        client_socket.close()
        return

    if username not in all_users:
        blocked_IPs[client_socket.getpeername()[0]] = time.datetime.now()
        client_socket.send('#terminate Invalid username. Your IP address has been blocked for %d seconds.'
                           % BLOCK_DURATION)
        client_socket.close()
        return

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
        user_entry = {'time': time.datetime.now(), 'socket': client_socket, 'lastActive': time.datetime.now()}
        login_history[username] = user_entry
        client_socket.send('#accepted Welcome to the intergalactic chat service!')

        # add to list of online users
        users_online.append(username)

        # broadcast login notification
        broadcast(username, '%s logged in' % username, True)

        # send offline messages
        if username in offline_msgs:
            for msg in offline_msgs[username]:
                send_info(username, msg)
            del offline_msgs[username]

        # serve client
        thread = threading.Thread(target=serve_client, args=(client_socket, username))
        thread.daemon = True
        thread.start()

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
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
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
            timeSinceActivity = login_history[user]['lastActive']
            time_now = time.datetime.now()
            time_elapsed = time_now - timeSinceActivity

            if time_elapsed.seconds > TIMEOUT:
                # close connection to timed out user
                user_sock = login_history[user]['socket']
                user_sock.send('#terminate timeout')
                user_sock.close()

                users_online.remove(user)
                broadcast(user, '%s was disconnected due to inactivity.' % user, True)


if __name__ == '__main__':
    cmdArgs = sys.argv
    if len(cmdArgs) != 4:
        print 'Usage: python server.py <server_port> <block_duration> <timeout>'
    else:
        # set variables
        SERVER_PORT = int(cmdArgs[1])
        BLOCK_DURATION = int(cmdArgs[2])
        TIMEOUT = int(cmdArgs[3])
        start_server()
