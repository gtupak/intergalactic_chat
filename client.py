# using python2.7

"""
Client should the following in order:
    - server_IP
    - server_port
"""

import sys, threading
from socket import *

connection_closed = False


def close_connection():
    global connection_closed
    connection_closed = True
    sock.close()


def listen_for_messages():
    global connection_closed
    try:
        while 1:
            server_msg = sock.recv(1024)
            if server_msg == '':
                # empty string most likely means that the server has shut down
                print 'PANIC: RECEIVED EMPTY STRING. SHUTTING DOWN'
                raise KeyboardInterrupt

            server_msg = server_msg.split()
            command = server_msg[0]
            if command == '#prompt':
                usr_input = raw_input('> %s ' % server_msg[1])
                sock.send(usr_input)
            elif command == '#info':
                print '> %s' % ' '.join(server_msg[1:])
            elif command == '#accepted':
                print '> %s' % ' '.join(server_msg[1:])

                # start chat thread
                writing_thread = threading.Thread(target=write_msg_listener)
                writing_thread.daemon = True
                writing_thread.start()
            elif command == '#terminate':
                print '> %s\nClosing socket' % ' '.join(server_msg[1:])
                close_connection()
                break
            else:
                # TODO figure out what to do when we don't recognize the command
                print '> %s\nClosing socket' % ' '.join(server_msg)
                close_connection()
                break
    except KeyboardInterrupt:
        # shut down writing thread
        print('Keyboard interrupt raised')
        close_connection()


def write_msg_listener():
    while 1:
        # if connection_closed:
        #     print 'writing thread finished'
        #     break

        usr_input = raw_input()

        if connection_closed:
            return

        sock.send(usr_input)




# def start_chat(server_ip, server_port):
#     sock = socket(AF_INET, SOCK_STREAM)
#     try:
#         sock.connect((server_ip, server_port))
#         listening_thread = threading.Thread(target=listen_for_messages, args=(sock,))
#         listening_thread.start()
#         listening_thread.join()
#
#     except error:
#         print 'Server is shut down. Terminating client'
#         sock.close()

if __name__ == '__main__':
    cmdArgs = sys.argv
    if len(cmdArgs) != 3:
        print 'Usage: client.py <server_IP> <server_port>'
    else:
        # get arguments
        server_ip = cmdArgs[1]
        server_port = int(cmdArgs[2])

        # start server
        sock = socket(AF_INET, SOCK_STREAM)
        try:
            sock.connect((server_ip, server_port))

            listening_thread = threading.Thread(target=listen_for_messages)
            listening_thread.daemon = True
            listening_thread.start()

            listening_thread.join()
            print 'listening thread finished'

        except error:
            print 'Server is shut down. Terminating client'
            sock.close()
