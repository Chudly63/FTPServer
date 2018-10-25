#!/usr/bin/env python
# CS472 - Homework #3 - FTP Server
# Alex M Brown
# FTPServer.py
#
# Concurrent FTP server that supports a small list of FTP commands

from socket import *
from threading import Thread
from requestParser import parseCommand
from Responses import responseCode
import argparse
import platform
import sys
import csv
import os

CLIENTS = []
USER_FILE = "users.csv"
BUFFER_SIZE = 1024
PORT_NUM = None
LOG_FILE = None
VERBOSE = False
USERS = {}
CRLF = "\r\n"

#[Errno 98] Address already in use

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
            self.command = self.sock.recv(BUFFER_SIZE)
            if self.command == "":
                return None
            return self.command
        except:
            return None  

    def sendResponse(self, msg):
        try:
            self.sock.send(msg + CRLF)
            return True
        except:
            return False


    def ftp_user(self):
        if not self.state == "Prompt USER":
            self.sendResponse(responseCode[503])
        else:
            self.user = self.myCommand[1]
            self.state = "Prompt PASS"
            self.sendResponse(responseCode[331])

    def ftp_pass(self):
        if not self.state == "Prompt PASS":
            self.sendResponse(responseCode[503])
        elif not self.user in USERS.keys():
            self.sendResponse(responseCode[530])
            self.state = "Prompt USER"
        elif self.myCommand[1] == USERS[self.user]:
            self.state = "Main"
            self.authenticated = True
            self.sendResponse(responseCode[230])
        else:
            self.sendResponse(responseCode[530])
            self.state = "Prompt USER"

    def ftp_cwd(self):
        self.sendResponse(responseCode[502])

    def ftp_quit(self):
        self.sendResponse(responseCode[502])

    def ftp_pasv(self):
        self.sendResponse(responseCode[502])

    def ftp_epsv(self):
        self.sendResponse(responseCode[502])

    def ftp_port(self):
        self.sendResponse(responseCode[502])

    def ftp_eprt(self):
        self.sendResponse(responseCode[502])

    def ftp_retr(self):
        self.sendResponse(responseCode[502])

    def ftp_stor(self):
        self.sendResponse(responseCode[502])

    def ftp_pwd(self):
        if not self.authenticated:
            self.sendResponse(responseCode[530])
        elif not self.state == "Main":
            self.sendResponse(responseCode[503])
        else:
            self.sendResponse("257 " + str(self.directory) + " is the current working directory")

    def ftp_list(self):
        self.sendResponse(responseCode[502])

    def ftp_syst(self):
        if not self.authenticated:
            self.sendResponse(responseCode[530])
        elif not self.state == "Main":
            self.sendResponse(responseCode[503])
        else:
            self.sendResponse("215 " + str(platform.system()))
        
    def ftp_help(self):
        self.sendResponse(responseCode[502])

    def run(self):

        self.SUPPORTED_COMMANDS = {
            "USER" : self.ftp_user,
            "PASS" : self.ftp_pass,
            "CWD"  : self.ftp_cwd,
            "QUIT" : self.ftp_quit,
            "PASV" : self.ftp_pasv,
            "EPSV" : self.ftp_epsv,
            "PORT" : self.ftp_port,
            "EPRT" : self.ftp_eprt,
            "RETR" : self.ftp_retr,
            "STOR" : self.ftp_stor,
            "PWD"  : self.ftp_pwd,
            "LIST" : self.ftp_list,
            "SYST" : self.ftp_syst,
            "HELP" : self.ftp_help
        }

        while True:
            self.myCommand = self.readCommand()
            if self.myCommand == None:
                self.sock.close()
                break
            else:
                self.myCommand = parseCommand(self.myCommand)

            print(self.myCommand)

            if self.myCommand == None:
                self.sendResponse(responseCode[500])

            elif self.myCommand == -1:
                self.sendResponse(responseCode[501])
            elif self.myCommand[0] in self.SUPPORTED_COMMANDS.keys():
                self.SUPPORTED_COMMANDS[self.myCommand[0]]()
            else:
                self.sendResponse(responseCode[502])



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
    global CLIENTS
    initializeGlobals()

    RECV_SOCKET = socket(AF_INET, SOCK_STREAM)
    RECV_SOCKET.bind(('',PORT_NUM))
    RECV_SOCKET.listen(5)
    print("Ready...")
    while True:
        newSocket, newAddress = RECV_SOCKET.accept()
        print("Connection from " + str(newAddress))
        newClient = FTPClient(newAddress[0], newAddress[1], newSocket)
        CLIENTS.append(newClient)
        newSocket.send("220 Welcome to Alex's FTP Server\r\n")
        newClient.start()



if __name__ == '__main__':
    main()

