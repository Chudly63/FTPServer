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
LOCAL_IP = ""
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
        self.active = True
        self.data_address = None
        self.state = "Prompt USER" 
        self.authenticated = False
        self.directory = MAIN_PATH  
        self.DATA_SOCKET = None

    """Create a socket and connect it to address"""
    def establishConnection(self, address):
        self.CONNECTION = socket(AF_INET, SOCK_STREAM)
        log("(" + self.ip + ", " + str(self.port) + ") NOTE: Establishing connection to " + str(address))
        try:
            self.CONNECTION.settimeout(5)
            self.CONNECTION.connect(address)
            log("(" + self.ip + ", " + str(self.port) + ") NOTE: Connection established with " + str(address))
            return self.CONNECTION
        except:
            log("(" + self.ip + ", " + str(self.port) + ") NOTE: Failed to establish connection")
            return None

    """Accept a connection from listener and return the socket of the connection"""
    def receiveConnection(self, listener):
        self.CONNECTION = socket(AF_INET, SOCK_STREAM)
        log("(" + self.ip + ", " + str(self.port) + ") NOTE: Accepting connection on " + str(listener.getsockname()))
        try:
            listener.settimeout(5)
            self.CONNECTION, self.addr = listener.accept()
            log("(" + self.ip + ", " + str(self.port) + ") NOTE: Accepted connection from " + str(self.addr))
            return self.CONNECTION
        except:
            log("(" + self.ip + ", " + str(self.port) + ") NOTE: Failed to receive connection")
            return None
        
    """Reads all data from socket"""
    def recvall(self, socket):
        log("(" + self.ip + ", " + str(self.port) + ") READ: DATA OVER DATA CONNECTION")
        self.data = b''
        while(True):
            self.resp = socket.recv(BUFFER_SIZE)
            if len(self.resp) == 0:
                return self.data
            else:
                self.data += self.resp


    """Read all data from socket and store it in a file"""
    def readFile(self, filename, socket):
        try:
            self.newFile = open(filename, "wb")
        except:
            return False
        self.newFile.write(self.recvall(socket).replace(CRLF, "\n"))
        self.newFile.close()
        return True
 

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

    """Send data over the data connection"""
    def sendData(self, data):
        try:
            log("(" + self.ip + ", " + str(self.port) + ") SENT: DATA OVER DATA CONNECTION")
            self.DATA_SOCKET.send(data + CRLF)
            return True
        except:
            return False

    """Send the contents of a file over the socket"""
    def sendFile(self, filename, socket):
        try:
            self.myFile = open(filename, "rb")
        except:
            return False
        log("(" + self.ip + ", " + str(self.port) + ") SENT: DATA OVER DATA CONNECTION")
        self.sendBuffer = self.myFile.read(BUFFER_SIZE)
        while not self.sendBuffer == "":
            socket.send(self.sendBuffer.replace("\n", CRLF))
            self.sendBuffer = self.myFile.read(BUFFER_SIZE)
        self.myFile.close()
        return True

    """Converts permissions number from os.stat into a string representation : ex. -rwx-rw-rw-"""
    def convertPermissions(self, num):
        self.permCodes = {'7':'rwx', '6' : 'rw-', '5' : 'r-x', '4' : 'r--', '3': '-wx', '2' : '-w-', '1' : '--x', '0' : '---'}
        self.permString = 'd' if stat.S_ISDIR(num) else '-'

        self.permissions = str(oct(num)[-3:])
        for self.p in self.permissions:
            self.permString += self.permCodes[self.p]

        return self.permString


    """Get the full listing information for myFile"""
    def getFileListing(self, myFile):
        self.fileInfo = os.stat(myFile)
        self.filePermissions = self.convertPermissions(self.fileInfo[0])
        self.fileLinks = str(self.fileInfo[3])
        self.fileOwner = str(self.fileInfo[4])
        self.fileGroup = str(self.fileInfo[5])
        self.fileSize = str(self.fileInfo[6])
        self.fileModified = datetime.datetime.fromtimestamp(self.fileInfo[8]).strftime("%b %d %H:%M")
        self.fileName = os.path.basename(myFile)
        return self.filePermissions + "\t" + self.fileLinks + " " + self.fileOwner + "\t" + self.fileGroup + "\t" + self.fileSize + "\t" + self.fileModified + "\t" + self.fileName + CRLF


    """Get the full listing information for every file/directory in the current directory"""
    def getDirectoryListing(self, directory):
        self.Listing = ""
        for self.f in sorted(os.listdir(directory)):
            self.Listing += self.getFileListing(os.path.join(directory, self.f))
        
        return self.Listing

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
            log("(" + self.ip + ", " + str(self.port) + ") NOTE: Logged in as: " + self.user)
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
        #Verify state of the client
        if not self.state == "Main":
            self.sendResponse(responseCode[503])
        #Verify the client is authenticated
        elif not self.authenticated:
            self.sendResponse(responseCode[530])
        else:
            #If the current directory is the root of the FTP environment, send error
            if self.directory == MAIN_PATH:
                self.sendResponse(responseCode[550])
            else:
                #Move to parent directory
                self.directory = os.path.split(self.directory)[0]
                self.sendResponse(responseCode[250])

    """FTP QUIT COMMAND"""
    def ftp_quit(self):
        self.sendResponse(responseCode[221])
        if self.DATA_SOCKET:
            self.DATA_SOCKET.close()
        if self.sock:
            self.sock.close()

    #DATA TRANSFER COMMANDS

    """FTP PASV COMMAND"""
    def ftp_pasv(self):
        #Verify the state of the client
        if not self.state == "Main":
            self.sendResponse(responseCode[503])
        #Verify the client is authenticated
        elif not self.authenticated:
            self.sendResponse(responseCode[530])
        else:
            #Open the Data Socket & bind it to an open port
            self.DATA_SOCKET = socket(AF_INET, SOCK_STREAM)
            self.DATA_SOCKET.bind((LOCAL_IP, 0))
            self.active = False

            #Get the header information (h1,h2,h3,h4,p1,p2)
            self.DATA_PORT = int(self.DATA_SOCKET.getsockname()[1])
            self.p2 = self.DATA_PORT % 256
            self.p1 = (self.DATA_PORT - self.p2) / 256
            self.h = ','.join(LOCAL_IP.split('.'))
            self.headers = "(" + self.h + ',' + str(self.p1) + ',' + str(self.p2) + ")."

            #Listen on the socket
            self.DATA_SOCKET.listen(1)

            #Send the header information to the client
            self.sendResponse(responseCode[227] + self.headers)
        

    """FTP EPSV COMMAND"""
    def ftp_epsv(self):
        self.sendResponse(responseCode[502])

    """FTP PORT COMMAND"""
    def ftp_port(self):
        #Verify the state of the client
        if not self.state == "Main":
            self.sendResponse(responseCode[503])
        #Verify the client is authenticated
        elif not self.authenticated:
            self.sendResponse(responseCode[530])
        else:
            #Enable active mode (Server initiates data connection on requests)
            self.active = True
            #Read the headers sent from the client (h1,h2,h3,h4,p1,p2)
            #The address for the server to connect to is h1.h2.h3.h4 on port 256*p1 + p2
            self.port_headers = self.myCommand[1].split(',')
            self.data_ip = '.'.join(self.port_headers[0:4])
            self.data_port = int(self.port_headers[4]) * 256 + int(self.port_headers[5])
            #Store the address of the client's data socket for connection upon request
            self.data_address = (self.data_ip, self.data_port)
            self.DATA_SOCKET = socket(AF_INET, SOCK_STREAM)
        
            self.sendResponse(responseCode[200])

    """FTP EPRT COMMAND"""
    def ftp_eprt(self):
        self.sendResponse(responseCode[502])

    """FTP RETR COMMAND"""
    def ftp_retr(self):
        #Verify the state of the client
        if not self.state == "Main":
            self.sendResponse(responseCode[503])
        #Verify the client is authenticated
        elif not self.authenticated:
            self.sendResponse(responseCode[530])
        else:
            #Get the path of the requested file
            self.retr_file = os.path.realpath(os.path.join(self.directory, self.myCommand[1]))

            #Check that the file exists, that it is a file, and that it is located within the FTP environment
            if not (os.path.exists(self.retr_file) and os.path.isfile(self.retr_file) and self.retr_file.startswith(MAIN_PATH)):
                self.sendResponse(responseCode[550])
                return

            if self.active:
                #Connect to the client
                self.DATA_SOCKET = self.establishConnection(self.data_address)
            else:
                #Accept connection from the client
                self.DATA_SOCKET = self.receiveConnection(self.DATA_SOCKET)

            if not self.DATA_SOCKET:
                #Connection failed
                self.sendResponse(responseCode[425])
            else:
                #Send the data
                self.sendResponse(responseCode[150])
                if self.sendFile(self.retr_file, self.DATA_SOCKET):
                    self.sendResponse(responseCode[226])
                else:
                    self.sendResponse(responseCode[426])
                
                self.DATA_SOCKET.close()
                self.DATA_SOCKET = None
            


    """FTP STOR COMMAND"""
    def ftp_stor(self):
        #Verify the state of the client
        if not self.state == "Main":
            self.sendResponse(responseCode[503])
        #Verify the client is authenticated
        elif not self.authenticated:
            self.sendResponse(responseCode[530])
        else:
            #Get the path for the file to be stored
            self.stor_file = os.path.realpath(os.path.join(self.directory, self.myCommand[1]))
            
            #Verify the path is within the FTP environment
            if not self.stor_file.startswith(MAIN_PATH):
                self.sendResponse(responseCode[553])
                return

            if self.active:
                #Connect to client's data port
                self.DATA_SOCKET = self.establishConnection(self.data_address)
            else:
                #Accept a connection from the client
                self.DATA_SOCKET = self.receiveConnection(self.DATA_SOCKET)

            if not self.DATA_SOCKET:
                #Connection failed
                self.sendResponse(responseCode[425])
            else:
                #Read data
                self.sendResponse(responseCode[150])
                if self.readFile(self.stor_file, self.DATA_SOCKET):
                    self.sendResponse(responseCode[226])
                else:
                    self.sendResponse(responseCode[426])
                
                self.DATA_SOCKET.close()
                self.DATA_SOCKET = None


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
        #Verify the state of the client
        if not self.state == "Main":
            self.sendResponse(responseCode[503])
        #Verify the client is authenticated
        elif not self.authenticated:
            self.sendResponse(responseCode[530])
        #Verify that a data connection is prepared
        elif not self.DATA_SOCKET:
            self.sendResponse(responseCode[425])
        else:
            #Check if the list parameter is a valid file/directory
            self.listData = ""
            self.directoryToRead = ""
            #No optional parameter
            if len(self.myCommand) == 1:
                #Print currend directory
                self.directoryToRead = self.directory
            else:
                #Get full path of parameter
                self.directoryToRead = os.path.join(self.directory, self.myCommand[1])
            
            #Make sure the path exists
            if os.path.exists(self.directoryToRead):
                self.directoryToRead = os.path.realpath(self.directoryToRead)
                #Make sure the path is in the FTP environment
                if self.directoryToRead.startswith(MAIN_PATH):
                    #Is the path a directory?
                    if os.path.isdir(self.directoryToRead):
                        self.listData = self.getDirectoryListing(self.directoryToRead)
                    #Is the path a file?
                    elif os.path.isfile(self.directoryToRead):
                        self.listData = self.getFileListing(self.directoryToRead)

                
            if self.active:
                #Connect to client's data port
                self.DATA_SOCKET = self.establishConnection(self.data_address)
            else:
                #Accept a connection from the client
                self.DATA_SOCKET = self.receiveConnection(self.DATA_SOCKET)

            #Was the data connection opened correctly?
            if not self.DATA_SOCKET:
                #Failed to open connection
                self.sendResponse(responseCode[425])
            else:
                self.sendResponse(responseCode[150])
                if self.sendData(self.listData.rstrip(CRLF)):
                    #Data sent OK
                    self.sendResponse(responseCode[226])
                else:
                    #Data failed to send
                    self.sendResponse(responseCode[426])

                log("(" + self.ip + ", " + str(self.port) + ") NOTE: Data connection closed")
                self.DATA_SOCKET.close()
                self.DATA_SOCKET = None


    """FTP SYST COMMAND"""
    def ftp_syst(self):
        #Verify the client is authenticated
        if not self.authenticated:
            self.sendResponse(responseCode[530])
        #Verify the state of the client
        elif not self.state == "Main":
            self.sendResponse(responseCode[503])
        else:
            #Send system information
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
Get the IP of the machine the script is running on.
Running gethostbyname() and gethostname() doesn't seem to work on Ubuntu, so I have to do it this way.
Create a connection to some public server and read the source IP of the connection
"""
def getMyIP():
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.connect(("8.8.8.8", 80))
    myIP = sock.getsockname()[0]
    sock.close()
    return myIP



"""
Parse the command line arguments and set the global values
"""
def initializeGlobals():
    global LOG_FILE, PORT_NUM, VERBOSE, USERS, LOCAL_IP
    parser = argparse.ArgumentParser(description = "FTP Server written by Alex M Brown.", epilog = 'Later Sk8r \m/(>.<)')
    parser.add_argument('-v', '--verbose', action='store_true', help="Print logging information to stdout. Useful for debugging.")
    parser.add_argument('LOG_FILE', help="The name of the file for the server logs.")
    parser.add_argument('PORT_NUM', type = int, help = "The port number for the server to run on.")
    args = vars(parser.parse_args(sys.argv[1:]))

    LOG_FILE = args['LOG_FILE']
    PORT_NUM = args['PORT_NUM']
    VERBOSE = args['verbose']

    USERS = populateUsers(USER_FILE)
    LOCAL_IP = getMyIP()



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
    RECV_SOCKET.bind(('0.0.0.0',PORT_NUM))
    RECV_SOCKET.listen(5)
    print("Ready...")
    log("SERVER IP ADDRESS: " + LOCAL_IP)
    log("SERVER LISTENING ON SOCKET: " + str(RECV_SOCKET.getsockname()))
    while True:
        #Accept a connection and create an FTPClient object for the new connection
        newSocket, newAddress = RECV_SOCKET.accept()
        log("(" + newAddress[0] + ", " + str(newAddress[1]) + ") NOTE: CONNECTED")
        newClient = FTPClient(newAddress[0], newAddress[1], newSocket)
        CLIENTS.append(newClient)
        newSocket.send("220 Welcome to Alex's FTP Server\r\n")
        newClient.start()
        CLIENTS = [c for c in CLIENTS if c.isAlive()]   #Remove disconnected clients
        log("SERVER IS CURRENTLY SERVING " + str(len(CLIENTS)) + " CLIENT(S)")



if __name__ == '__main__':
    main()

