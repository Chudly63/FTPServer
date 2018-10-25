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
import csv
import os

Clients = []
USER_FILE = "users.csv"
BUFFER_SIZE = 1024
PORT_NUM = None
LOG_FILE = None
VERBOSE = False
USERS = {}
CRLF = "\r\n"


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
        self.user = None
        self.state = "Prompt USER" 
        self.authenticated = False
        self.directory = os.getcwd()

    def readCommand(self):
        try:
            command = self.sock.recv(BUFFER_SIZE)
            if command == "":
                return None
            return command
        except:
            return None  

    def sendResponse(self, msg):
        try:
            self.sock.send(msg + CRLF)
            return True
        except:
            return False


    def run(self):
        while True:
            myCommand = self.readCommand()
            if myCommand == None:
                self.sock.close()
                break
            else:
                myCommand = parseCommand(myCommand)
            print(myCommand)

            if myCommand == None:
                self.sendResponse("502 Command not implemented.")

            elif myCommand == -1:
                self.sendResponse("501 Syntax error in parameters.")


            elif myCommand[0] == "USER":
                if not self.state == "Prompt USER":
                    self.sendResponse("503 Bad sequence of commands.")
                else:
                    self.user = myCommand[1]
                    self.state = "Prompt PASS"
                    self.sendResponse("331 User OK, need password.")


            elif myCommand[0] == "PASS":
                if not self.state == "Prompt PASS":
                    self.sendResponse("503 Bad sequence of commands.")
                elif not self.user in USERS.keys():
                    self.sendResponse("530 Failed to authenticate user.")
                    self.state = "Prompt USER"
                elif myCommand[1] == USERS[self.user]:
                    self.state = "Main"
                    self.authenticated = True
                    self.sendResponse("230 User logged in, proceed.")
                else:
                    self.sendResponse("530 Failed to authenticate user.")
                    self.state = "Prompt USER"





def log(message):
    if VERBOSE:
        print(message)



def populateUsers(user_file):
    try:
        with open(user_file, "rb") as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                USERS[row[0]] = row[1]
        return USERS
    except IOError:
        log("FATAL ERROR: USER AUTHENTICATION FILE MISSING")
        exit()
    except IndexError:
        log("FATAL ERROR: INVALID USER FILE")
        exit()



def initializeGlobals():
    global LOG_FILE, PORT_NUM, VERBOSE, USERS
    parser = argparse.ArgumentParser(description = "FTP Server written by Alex M Brown.", epilog = 'Later Sk8r \m/(>.<)')
    parser.add_argument('-v', '--verbose', action='store_true', help="Print logging information to stdout. Useful for debugging.")
    parser.add_argument('LOG_FILE', help="The name of the file for the server logs.")
    parser.add_argument('PORT_NUM', type = int, help = "The port number for the server to run on.")
    args = vars(parser.parse_args(sys.argv[1:]))

    LOG_FILE = args['LOG_FILE']
    PORT_NUM = args['PORT_NUM']
    VERBOSE = args['verbose']

    USERS = populateUsers(USER_FILE)



def main():
    initializeGlobals()

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

