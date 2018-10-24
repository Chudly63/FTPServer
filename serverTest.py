from threading import Thread
from socket import *

class ServerThread(Thread):
    def __init__(self, ip, port, sock):
        Thread.__init__(self)
        self.client_ip = ip
        self.client_port = port
        self.client_sock = sock

    def run(self):
        print(self.client_ip)
        print(self.client_port)
        print(self.client_sock)
        self.client_sock.send("200 Wassup Boi?\r\n")
        test = self.client_sock.recv(1024)
        print("Received: " + test)
        self.client_sock.send(str(self.client_port) + "\r\n")



def main():
    CLIENTS = []
    RECV_SOCKET = socket(AF_INET, SOCK_STREAM)
    HOST = "127.0.0.1"
    PORT = 21002
    RECV_SOCKET.bind((HOST,PORT))
    RECV_SOCKET.listen(5)
    print("Ready...")
    while True:
        conn, addr = RECV_SOCKET.accept()
        print("Connection from " + str(addr[1]))
        client = ServerThread(addr[0], addr[1], conn)
        CLIENTS.append(client)
        client.start()


if __name__ == '__main__':
    main()
