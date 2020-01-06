import threading
import socket
import pickle
import time
import os

from colorama import init
from colorama import Fore, Back, Style
init()

from playsound import playsound

# GLOBAL variables

HEADER_SIZE = 10
IP = socket.gethostname()
PORT = 5555
CMD_PORT = 6000
ENCRYPT_PORT = 6500
connected_users = {}
cmd_connections = {}
encrypt_connections = {}

# GLOBAL variables

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', PORT))
server_socket.listen(10)

command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
command_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
command_socket.bind(('', CMD_PORT))
command_socket.listen(10)

encrypt_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
encrypt_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
encrypt_socket.bind(('', ENCRYPT_PORT))
encrypt_socket.listen(10)


class Chat(object):
    """
    For every client that connects we create
    his own Chat instance and we handle that client.
    """

    def __init__(self, conn, addr, cmd_conn, encrypt_conn):
        self.conn = conn
        self.addr = addr
        self.cmd_conn = cmd_conn
        self.encr_conn = encrypt_conn
        self.username = ''

    def get_username(self):
        """
        On this method we receive a message that is the
        username that our client picked, we check if that
        username exists already, if it does then we deny it
        and if not we store the username with the associated
        socket connections (msg_conn and cmd_conn)
        """

        try:
            self.username = conn.recv(1024).decode("utf-8")
            self.username = self.username[HEADER_SIZE:]

            if self.username in connected_users:
                self.conn.send('DENIED'.encode("utf-8"))
                self.get_username()
            else:
                self.conn.send("ACCEPTED".encode("utf-8"))
                connected_users[self.username] = self.conn
                cmd_connections[self.username] = self.cmd_conn
                encrypt_connections[self.username] = self.encr_conn
                print(f' [+] {Fore.GREEN}{self.username}{Style.RESET_ALL} from {Fore.GREEN}{self.addr}{Style.RESET_ALL} just joined the server!')
                time.sleep(0.5)
                self.send_spec()
                return False

        except (ConnectionResetError, ConnectionResetError):
            self.send_spec()
            print(f' [+] {self.addr} prematurely left the server!')
            return True


    def runThread(self):
        """
        On this method we start a thread that will listen to the messages
        of only one client, each client has its own socket "channel" so no
        interference occurs.
        """

        receiver = threading.Thread(target=self.receive_msg)
        receiver.start()

    def receive_msg(self):
        """
        The main thread resides here, we put the main thread to loop for ever
        until the connection with the server is closed, the way we receive messages
        is using HEADERS, we include a header in each message we want to send that
        includes the size of the message the header size (10) and the actual message
        The message looks like this: 54.........Whats up buddy, long time no see.
        The dots are the header size(10) so we can send and receive data up to 10.000.000.000 characters long.
        If the connection closes then we remove the username and connection from our list and we
        send the list of online users to all our clients.
        """

        new_msg = True
        full_msg = ''
        msg_size = 0

        while True:
            try:
                msg = self.conn.recv(HEADER_SIZE).decode("utf-8")

                if msg:

                    if new_msg:
                        msg_size = int(msg[:HEADER_SIZE])
                        new_msg = False

                    full_msg += msg

                    if len(full_msg) - HEADER_SIZE == msg_size:
                        self.broadcast_msg(full_msg)
                        new_msg = True
                        full_msg = ''
                else:
                    raise ConnectionResetError

            except (ConnectionResetError, ConnectionAbortedError):
                del connected_users[self.username]
                del cmd_connections[self.username]
                self.send_spec()
                server_msg = self.add_header(f' [+] SERVER --> {self.username} just left the server!')
                self.broadcast_msg(server_msg)
                print(f' [+] {self.username} just left the server!')
                break


    def add_header(self, msg):
        header_msg = f'{len(msg):<{HEADER_SIZE}}' + msg
        return header_msg

    def broadcast_msg(self, msg):
        """
        When we receive a message successfully we pass our message
        to this method and it sends the message to all users
        excluding the user that sent it.
        """

        for user in connected_users:
            if user != self.username:
                connected_users[user].send(msg.encode("utf-8"))
        print(f' [+] Message broadcast completed!')


    def send_spec(self):
        """
        Once this method is called, it pickles the list of connected
        users, adds the length of the data first, then the header size
        as dots and then the pickled list of users online and sends it
        to every user, this function is called once on every instance of
        the server when a client disconnects or connects.
        """
        try:
            global cmd_connections
            data = pickle.dumps(list(connected_users.keys()))
            data = f'{len(data):<{HEADER_SIZE}}'.encode("utf-8") + data

            for cmd_user in list(cmd_connections.keys()):
                cmd_connections[cmd_user].send(data)

            print(f' [+] Broadcasted users online')



        except ConnectionResetError:
            pass




print(f' [+] Waiting for an incoming connection..')

while True:
    conn, addr = server_socket.accept()
    cmd_conn, _ = command_socket.accept()
    encrypt_conn, _ = encrypt_socket.accept()
    client = Chat(conn, addr, cmd_conn, encrypt_conn)
    got_error = client.get_username()

    if not got_error:
        client.runThread()