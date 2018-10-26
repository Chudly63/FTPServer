import os
import stat
import datetime

FILETREE_CAP = os.path.realpath("ROOT")
CURRENT = os.path.realpath("ROOT")

def printFile(file):
    with open(file, "r+") as script:
        lines = script.readlines()
        for line in lines:
            print(line[:-1])


def convertPerm(num):
    permCodes = {'7':'rwx', '6' : 'rw-', '5' : 'r-x', '4' : 'r--', '3': '-wx', '2' : '-w-', '1' : '--x', '0' : '---'}
    
    permString = 'd' if stat.S_ISDIR(num) else '-'

    permissions = str(oct(num)[-3:])
    for p in permissions:
        permString += permCodes[p]

    return permString


    

def main():
    global CURRENT, FILETREE_CAP
    while(True):
        current_display = "FTP" + CURRENT[len(FILETREE_CAP):]
        choice = raw_input(current_display + "> ")
        if choice == "cdup":
            if CURRENT == FILETREE_CAP:
                print("No can do")
            else:
                CURRENT = os.path.split(CURRENT)[0]
        if choice == "cd":
            myDir = raw_input("Directory?> ")
            myDirPath = os.path.join(CURRENT,myDir)
            if os.path.exists(myDirPath) and os.path.isdir(myDirPath):
                CURRENT = os.path.realpath(myDirPath)
            else:
                print("IDK man")
        if choice == "ls":
            #Permissions | number of links | owner | group | size | last modified | name
            for f in sorted(os.listdir(CURRENT)):
                info = os.stat(os.path.join(CURRENT, f))
                myPerms = convertPerm(info[0])
                myLinks = str(info[3])
                myOwner = str(info[4])
                myGroup = str(info[5])
                mySize = str(info[6])
                myModified = datetime.datetime.fromtimestamp(info[8]).strftime("%b %d %H:%M")
                myName = f
                print(myPerms + "\t" + myLinks + " " + myOwner + "\t" + myGroup + "\t" + mySize + "\t" + myModified + "\t" + myName)
        if choice == "cat":
            myFile = raw_input("File?> ")
            myFilePath = os.path.join(CURRENT,myFile)
            if os.path.exists(myFilePath) and os.path.isfile(myFilePath):
                printFile(myFilePath)
            else:
                print("Can't read that shit")
        if choice == "quit":
            exit()



if __name__ == '__main__':
    main()