# using python2.7

"""
Client should the following in order:
    - server_IP
    - server_port
"""

import sys, threading
from socket import *
from stoppableThread import *

global SERVER_IP, SERVER_PORT


def listen_for_messages(sock):
    try :
        while 1:
            server_msg = sock.recv(1024)
            if server_msg == '':
                # empty string most likely means that the server has shut down
                print 'PANIC: RECEIVED EMPTY STRING. SHUTTING DOWN'
                sock.close()
                break

            server_msg = server_msg.split()
            command = server_msg[0]
            if command == '#prompt':
                usr_input = raw_input('> %s ' % server_msg[1])
                sock.send(usr_input)
            elif command == '#info':
                print '> %s' % ' '.join(server_msg[1:])
            elif command == '#accepted':
                print '> %s' % ' '.join(server_msg[1:])
                # start listening thread
                listening_thread = StoppableThread(target=listen_for_messages, args=(sock,))
                listening_thread.start()

                # start chat thread
                writing_thread = StoppableThread(target=write_msg_listener, args=(sock,))
                writing_thread.start()
            elif command == '#terminate':
                print '> %s\nClosing socket' % ' '.join(server_msg[1:])
                sock.close()
            else:
                # TODO figure out what to do when we don't recognize the command
                print '> %s\nClosing socket' % ' '.join(server_msg)
                sock.close()
    except KeyboardInterrupt:
        # shut down writing thread
        writing_thread.stop()


def write_msg_listener(sock):
    while 1:
        if threading.current_thread().stopped():
            break

        usr_input = raw_input()
        sock.send(usr_input)


def start_chat():
    sock = socket(AF_INET, SOCK_STREAM)
    try:
        sock.connect((SERVER_IP, SERVER_PORT))
        thread = threading.Thread(target=listen_for_messages, args=(sock,))
        thread.start()

    except error:
        print 'Server is shut down. Terminating client'
        sock.close()

if __name__ == '__main__':
    cmdArgs = sys.argv
    if len(cmdArgs) != 3:
        print 'Usage: client.py <server_IP> <server_port>'
    else:
        global SERVER_IP, SERVER_PORT
        # set variables
        SERVER_IP = cmdArgs[1]
        SERVER_PORT = int(cmdArgs[2])
        start_chat()
