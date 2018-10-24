"""
requestParser.py
Alex M Brown
Parses FTP requests into lists containing the command name and any extra parameters
"""

def isInt(str):
    try:
        x = int(str)
        return True
    except:
        return False


#A return value of None represents a non-supported command
#A return value of -1 represents invalid syntax
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
            return -1
        else:
            return PARAMS

    #Verify commands with one parameter
    elif ARG in COMMANDS_WITH_ONE_PARAMETER:
        if (not len(args) == 2) or (args[1] == ""):
            return -1
        else:
            PARAMS.append(args[1])
            return PARAMS

    #Verify commands with optional parameters
    elif ARG in COMMANDS_WITH_OPTIONAL_PARAMETERS:
        if len(args) == 2:
            if args[1] == "":
                return -1
            else:
                PARAMS.append(args[1])
        elif len(args) > 2:
            return -1
        return PARAMS

    #Verify commands with special parameters
    #EPSV<sp><protocol><CRLF>
    elif ARG == "EPSV":
        if not len(args) == 2:
            return -1
        if not (args[1] == "1" or args[1] == "2"):
            return -1
        else:
            PARAMS.append(args[1])
            return PARAMS

    #PORT<sp><host-port><CRLF>
    elif ARG == "PORT":
        if not len(args) == 2:
            return -1
        hostport = args[1].split(',')
        if not len(hostport) == 6:
            return -1
        for i in hostport:
            if not isInt(i):
                return -1
        PARAMS.append(args[1])
        return PARAMS

    #EPRT<sp><d><protocol><d><address><d><port><d><CRLF>
    elif ARG == "EPRT":
        return "eprt"
        
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