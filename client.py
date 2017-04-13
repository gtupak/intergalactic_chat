# using python2.7

"""
Client should the following in order:
    - server_IP
    - server_port
"""

import sys
from socket import *

global SERVER_IP, SERVER_PORT


def start_chat():
    clientSocket = socket(AF_INET, SOCK_STREAM)
    try:
        clientSocket.connect((SERVER_IP, SERVER_PORT))

        while 1:
            server_msg = clientSocket.recv(1024)
            if server_msg == '':
                continue

            server_msg = server_msg.split()
            command = server_msg[0]
            if command == '#prompt':
                usr_input = raw_input('> %s ' % server_msg[1])
                clientSocket.send(usr_input)
            elif command == '#info':
                print '> %s' % ' '.join(server_msg[1:])
            elif command == '#terminate':
                print '> %s ' % ' '.join(server_msg[1:])
                clientSocket.close()
                break
            else:
                # TODO figure out what to do when we don't recognize the command
                print '> %s' % ' '.join(server_msg)
                clientSocket.close()
                break

    except KeyboardInterrupt:
        print 'KEYBOARD_INTERRUPT! Shutting down client gracefully'
        clientSocket.close()
    except error:
        print 'Server is shut down. Terminating client'
        clientSocket.close()

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
