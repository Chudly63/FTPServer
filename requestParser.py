#!/usr/bin/env python
# CS472 - Homework #3 - Request Parser
# Alex M Brown
# requestParser.py
#
# Parses strings representing FTP commands into a list containing the command and its parameters

"""Returns true if str can be converted to an Integer"""
def isInt(str):
    try:
        x = int(str)
        return True
    except:
        return False

"""
Parses a string into a list containing an FTP command and its parameters
Example: parseCommand("EPRT |1|127.0.0.1|21|") -> ['EPRT','1','127.0.0.1', '21']
Input:
    str command : A string representing an FTP command
Output:
    None : Non-Supported Command
    -1   : Invalid Command Syntax
    List : Contains FTP command and its parameters
"""
def parseCommand(command):
    COMMANDS_WITH_ONE_PARAMETER = ['USER', 'PASS', 'CWD', 'RETR', 'STOR'] 
    COMMANDS_WITH_NO_PARAMETERS = ['CDUP', 'QUIT', 'PASV', 'PWD', 'SYST'] 
    COMMANDS_WITH_OPTIONAL_PARAMETERS = ["LIST", "HELP"]

    command = command.rstrip(" \r\n")
    PARAMS = []
    args = command.split(" ")
    ARG = args[0].upper()
    PARAMS.append(ARG)

    #Verify commands with no parameters
    if ARG in COMMANDS_WITH_NO_PARAMETERS:
        if (not len(args) == 1):
            return -1                           #Invalid Command: Incorrect number of parameters
        else:
            return PARAMS

    #Verify commands with one parameter
    elif ARG in COMMANDS_WITH_ONE_PARAMETER:
        if (not len(args) == 2) or (args[1] == ""):
            return -1                           #Invalid Command: Incorrect number of parameters OR blank parameter
        else:
            PARAMS.append(args[1])
            return PARAMS

    #Verify commands with optional parameters
    elif ARG in COMMANDS_WITH_OPTIONAL_PARAMETERS:
        if len(args) == 2:
            if args[1] == "":
                return -1                       #Invalid Command: Blank parameter
            else:
                PARAMS.append(args[1])
        elif len(args) > 2:
            return -1                           #Invalid Command: Too many parameters
        return PARAMS

    #Verify commands with special parameters
    #EPSV<sp><protocol><CRLF>
    elif ARG == "EPSV":
        if not len(args) == 2:
            return -1                           #Invalid EPSV: Incorrect number of parameters
        if not (args[1] == "1" or args[1] == "2"):
            return -1                           #Invalid Protocol: Not a supported AF Number
        else:
            PARAMS.append(args[1])
            return PARAMS

    #PORT<sp><host-port><CRLF>
    elif ARG == "PORT":
        if not len(args) == 2:
            return -1                           #Invalid PORT: Incorrect number of parameters
        hostport = args[1].split(',')
        if not len(hostport) == 6:
            return -1                           #Invalid Headers: Incorrect number of headers
        for i in hostport:
            if not isInt(i):
                return -1                       #Invalid Header: Not a number
        PARAMS.append(args[1])
        return PARAMS

    #EPRT<sp><d><protocol><d><address><d><port><d><CRLF>
    elif ARG == "EPRT":
        if not len(args) == 2:
            return -1                           #Invalid EPRT syntax: No parameters OR too many spaces
        hostport = args[1].split("|")
        if not len(hostport) == 5:
            return -1                           #Invalid EPRT syntax: Incorrect number of parameters
        #Verify Protocol
        protocol = hostport[1]
        if not (protocol == "1" or protocol == "2"):
            return -1                           #Invalid AF Number

        #Verify IP
        address = hostport[2]
        if protocol == "1":
            address = address.split(".")
            if not len(address) == 4:
                return -1                       #Invalid IPv4 Address: Doesn't have 4 components
            for i in address:
                if not isInt(i):
                    return -1                   #Invalid IPv4 Address: Not composed of numbers
        elif protocol == "2":
            address = address.split(":")
            if not len(address) == 6:
                return -1                       #Invalid IPv6 Address: Doesn't have 6 components
                                                #We can end IPv6 checking here since our server won't even support it to begin with

        #Verify Port
        port = hostport[3]
        if not isInt(port):
            return -1                           #Invalid Port Number: Not a number
        
        PARAMS.append(hostport[1])
        PARAMS.append(hostport[2])
        PARAMS.append(hostport[3])
        return PARAMS
        
    #Not a supported command
    else:
        return None


def main():
    print("Write FTP commands:")
    while(True):
        test = raw_input("> ")
        print(parseCommand(test))


if __name__ == '__main__':
    main()