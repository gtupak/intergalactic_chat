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
    global x
    try:
        while 1 and not connection_closed:
            server_msg = sock.recv(1024)
            if server_msg == '':
                # empty string most likely means that the server has shut down
                raise KeyboardInterrupt

            server_msg = server_msg.split(' ')
            # command = server_msg[0]

            toPrint = ''
            for word in server_msg:
                if word != '' and word[0] == '#':
                    if word == '#prompt':
                        usr_input = raw_input('> %s\n' % ' '.join(server_msg[1:]))
                        sock.send(usr_input)
                        break

                    elif word == '#accepted':
                        print '> %s' % ' '.join(server_msg[1:])

                        # start chat thread
                        writing_thread = threading.Thread(target=write_msg_listener)
                        writing_thread.daemon = True
                        writing_thread.start()
                        break

                    elif word == '#terminate':
                        if len(server_msg) > 1:
                            print '> %s' % ' '.join(server_msg[1:])
                        close_connection()
                        break

                    elif word == '#info':
                        toPrint += '> '
                        # print '> %s' % ' '.join(server_msg[1:])

                    else:
                        # toPrint += word + ' '
                        print '> %s\nClosing socket' % ' '.join(server_msg)
                        close_connection()
                        break
                else:
                    toPrint += word + ' '

            if toPrint != '':
                print toPrint

    except KeyboardInterrupt:
        # shut down writing thread
        close_connection()


def write_msg_listener():
    while 1:
        usr_input = raw_input()

        if connection_closed:
            return

        sock.send(usr_input)


if __name__ == '__main__':
    cmdArgs = sys.argv
    if len(cmdArgs) != 3:
        print 'Usage: client.py <server_IP> <server_port>'
    else:
        # get arguments
        server_ip = cmdArgs[1]
        server_port = int(cmdArgs[2])

        # start client
        sock = socket(AF_INET, SOCK_STREAM)
        try:
            sock.connect((server_ip, server_port))

            listening_thread = threading.Thread(target=listen_for_messages)
            listening_thread.daemon = True
            listening_thread.start()

            listening_thread.join()

        except error:
            print 'Server is shut down. Terminating client'
            sock.close()
