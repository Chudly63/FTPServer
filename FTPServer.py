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
import datetime
import stat
import sys
import csv
import os

#Location of the FTP environment. Will be created if it does not exist

MAIN_PATH = os.path.join(os.getcwd(),"FTP_ROOT")    

#FTP environment will be a folder called FTP_ROOT that is located in the directory where FTPServer.py
#is being run. Clients will only be able to interact with files within this environment.

#Other GLOBALS
CLIENTS = []
USER_FILE = "users.csv"
BUFFER_SIZE = 1024
PORT_NUM = None
LOG_FILE = None
VERBOSE = False
USERS = {}
CRLF = "\r\n"

"""
Write message to the log file.
If running verbose, write message to stdout as well.
"""
def log(message):
    if VERBOSE:
        print("#LOG: " + message)
    with open(LOG_FILE, "a+") as logfile:
        logtime = str(datetime.datetime.now())[:-3]
        logfile.write(logtime + ": " + message + "\n")


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
        self.directory = MAIN_PATH

    """Read command from client"""
    def readCommand(self):
        try:
            self.command = self.sock.recv(BUFFER_SIZE)
            if self.command == "":
                return None
            log("(" + self.ip + ", " + str(self.port) + ") READ: " + self.command[:-2])
            return self.command
        except:
            return None  

    """Send response to client"""
    def sendResponse(self, msg):
        try:
            log("(" + self.ip + ", " + str(self.port) + ") SENT: " + msg)
            self.sock.send(msg + CRLF)
            return True
        except:
            return False

    #ACCESS CONTROL COMMANDS

    """FTP USER COMMAND"""
    def ftp_user(self):
        #Verify the state of the client
        if not self.state == "Prompt USER":
            self.sendResponse(responseCode[503])
        else:
            self.user = self.myCommand[1]
            self.state = "Prompt PASS"
            self.sendResponse(responseCode[331])

    """FTP PASS COMMAND"""
    def ftp_pass(self):
        #Verify the state of the client
        if not self.state == "Prompt PASS":
            self.sendResponse(responseCode[503])
        #Does the username of the client appear in the USER base?
        elif not self.user in USERS.keys():
            self.sendResponse(responseCode[530])
            self.state = "Prompt USER"
        #Is the password correct for the current user?
        elif self.myCommand[1] == USERS[self.user]:
            self.state = "Main"
            self.authenticated = True
            self.sendResponse(responseCode[230])
            log("(" + self.ip + ", " + str(self.port) + ") NOTE: User logged in: " + self.user)
        else:
            self.sendResponse(responseCode[530])
            self.state = "Prompt USER"

    """FTP CWD COMMAND"""
    def ftp_cwd(self):
        #Verify the state of the client
        if not self.state == "Main":
            self.sendResponse(responseCode[503])
        #Verify the client is authenticated
        elif not self.authenticated:
            self.sendResponse(responseCode[530])
        else:
            #Generate the path to the requested directory and verify it exists
            self.myDir = self.myCommand[1]
            self.myDirPath = os.path.join(self.directory, self.myDir)
            if os.path.exists(self.myDirPath) and os.path.isdir(self.myDirPath):
                #Generate the actual path to the directory. (Example: Converts Root/Dir1/../Dir2 into Root/Dir2)
                self.realDirPath = os.path.realpath(self.myDirPath)
                #Make sure the requested directory is within the FTP environment
                if not self.realDirPath.startswith(MAIN_PATH):
                    self.sendResponse(responseCode[550])
                else:
                    #Change the client's directory
                    self.directory = self.realDirPath
                    self.sendResponse(responseCode[250])
            else:
                self.sendResponse(responseCode[550])
    
    """FTP CDUP COMMAND"""
    def ftp_cdup(self):
        if not self.state == "Main":
            self.sendResponse(responseCode[503])
        elif not self.authenticated:
            self.sendResponse(responseCode[530])
        else:
            if self.directory == MAIN_PATH:
                self.sendResponse(responseCode[550])
            else:
                self.directory = os.path.split(self.directory)[0]
                self.sendResponse(responseCode[250])

    """FTP QUIT COMMAND"""
    def ftp_quit(self):
        self.sendResponse(responseCode[502])

    #DATA TRANSFER COMMANDS

    """FTP PASV COMMAND"""
    def ftp_pasv(self):
        self.sendResponse(responseCode[502])

    """FTP EPSV COMMAND"""
    def ftp_epsv(self):
        self.sendResponse(responseCode[502])

    """FTP PORT COMMAND"""
    def ftp_port(self):
        self.sendResponse(responseCode[502])

    """FTP EPRT COMMAND"""
    def ftp_eprt(self):
        self.sendResponse(responseCode[502])

    """FTP RETR COMMAND"""
    def ftp_retr(self):
        self.sendResponse(responseCode[502])

    """FTP STOR COMMAND"""
    def ftp_stor(self):
        self.sendResponse(responseCode[502])

    #SYSTEM COMMANDS

    """FTP PWD COMMAND"""
    def ftp_pwd(self):
        #Verify the state of the client
        if not self.state == "Main":
            self.sendResponse(responseCode[503])
        #Verify the user is authenticated
        elif not self.authenticated:
            self.sendResponse(responseCode[530])
        else:
            #When showing the current directory, only show the path extending from the 
            #root of the FTP environment directory
            self.showDir = self.directory[len(MAIN_PATH):]
            #If the current directory is the root of the FTP environment directory, indicate this with a /
            if self.showDir == "":
                self.showDir = "/"
            self.sendResponse("257 " + str(self.showDir) + " is the current working directory")

    """FTP LIST COMMAND"""
    def ftp_list(self):
        self.sendResponse(responseCode[502])

    """FTP SYST COMMAND"""
    def ftp_syst(self):
        if not self.authenticated:
            self.sendResponse(responseCode[530])
        elif not self.state == "Main":
            self.sendResponse(responseCode[503])
        else:
            self.sendResponse("215 " + str(platform.system()))
        
    """FTP HELP COMMAND"""
    def ftp_help(self):
        self.sendResponse(responseCode[502])

    """
    FTP CLIENT MAIN
    Continuously read and respond to commands from the client
    """
    def run(self):

        self.SUPPORTED_COMMANDS = {
            "USER" : self.ftp_user,
            "PASS" : self.ftp_pass,
            "CWD"  : self.ftp_cwd,
            "CDUP" : self.ftp_cdup,
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

            #Client disconnected from server
            if self.myCommand == None:
                log("(" + self.ip + ", " + str(self.port) + ") NOTE: DISCONNECTED")
                self.sock.close()
                break
            else:
                #Convert command into a list with format [COMMAND, PARAMETER1, PARAMETER2, ... ]
                self.myCommand = parseCommand(self.myCommand)

            print(self.myCommand)

            #Unrecognizable command
            if self.myCommand == None:
                self.sendResponse(responseCode[500])
            #Syntax error in command
            elif self.myCommand == -1:
                self.sendResponse(responseCode[501])
            #Supported command
            elif self.myCommand[0] in self.SUPPORTED_COMMANDS.keys():
                self.SUPPORTED_COMMANDS[self.myCommand[0]]()
            #Unsupported command
            else:
                self.sendResponse(responseCode[502])



"""
Read the USERS from the user_file
Input:
    user_file : csv file containing users and passwords
Output:
    dict : Dictionary with Keys = Users, Values = Passwords
"""
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


"""
Parse the command line arguments and set the global values
"""
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



"""
Main
Establish a receiving port.
Create an FTPClient object for each client that connects.
"""
def main():
    global CLIENTS

    #Set up an FTP environment if it does not already exist
    if not os.path.isdir(MAIN_PATH):
        os.makedirs(MAIN_PATH)

    initializeGlobals()

    log("------------------------------New Session------------------------------")

    RECV_SOCKET = socket(AF_INET, SOCK_STREAM)
    RECV_SOCKET.bind(('',PORT_NUM))
    RECV_SOCKET.listen(5)
    print("Ready...")
    log("SERVER LISTENING ON SOCKET: " + str(RECV_SOCKET.getsockname()))
    while True:
        newSocket, newAddress = RECV_SOCKET.accept()
        log("(" + newAddress[0] + ", " + str(newAddress[1]) + ") NOTE: CONNECTED")
        newClient = FTPClient(newAddress[0], newAddress[1], newSocket)
        CLIENTS.append(newClient)
        newSocket.send("220 Welcome to Alex's FTP Server\r\n")
        newClient.start()



if __name__ == '__main__':
    main()

