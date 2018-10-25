#!/usr/bin/env python
# CS472 - Homework #3 - FTP Server
# Alex M Brown
# FTPServer.py
#
# Concurrent FTP server that supports a small list of FTP commands

from socket import *
from threading import Thread
from requestParser import parseCommand
import argparse
import sys
import os

Clients = []
PORT_NUM = None
LOG_FILE = None
VERBOSE = False


"""
FTPClient Class. Extension of python's Thread class.
Each instantiation of this class represents a client. This class tracks information regarding that client
and executes server functionality for that client.
FTPClients run concurrently with each other. 
"""
class FTPClient(Thread):
    def __init__(self, ip, port, sock):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = sock
        self.authenticated = False
        self.directory = os.getcwd()

    def run(self):
        print(self.ip)
        print(self.port)


def main():

    parser = argparse.ArgumentParser(description = "FTP Server written by Alex M Brown.", epilog = 'Later Sk8r \m/(>.<)')
    parser.add_argument('-v', '--verbose', action='store_true', help="Print logging information to stdout. Useful for debugging.")
    parser.add_argument('LOG_FILE', help="The name of the file for the server logs.")
    parser.add_argument('PORT_NUM', type = int, help = "The port number for the server to run on.")
    args = vars(parser.parse_args(sys.argv[1:]))

    LOG_FILE = args['LOG_FILE']
    PORT_NUM = args['PORT_NUM']
    VERBOSE = args['verbose']

    RECV_SOCKET = socket(AF_INET, SOCK_STREAM)
    RECV_SOCKET.bind(('',PORT_NUM))
    RECV_SOCKET.listen(5)
    print("Ready...")
    while True:
        newSocket, newAddress = RECV_SOCKET.accept()
        print("Connection from " + str(newAddress))
        newClient = FTPClient(newAddress[0], newAddress[1], newSocket)
        Clients.append(newClient)
        newSocket.send("220 Welcome to Alex's FTP Server\r\n")
        newClient.start()

if __name__ == '__main__':
    main()

