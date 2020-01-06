import threading
import keyboard
import socket
import pickle
import webbrowser
import sys
import os

import cryptography
from cryptography.fernet import Fernet

from playsound import playsound
from colorama import init
from colorama import Fore, Back, Style
init()
# init for colorama

# GLOBAL variables
animation = 0
HEADER_SIZE = 10
IP = socket.gethostname()
PORT = 5555
CMD_PORT = 6000
ENCR_PORT = 6500

my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
command = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
encrypt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# GLOBAL variables


class Chat(object):
    """
    Class instance is used to connect and interact with the server
    """
    def __init__(self):
        self.username = ''
        self.encrypt_key = ''
        self.messages = []
        self.users_online = []
        self.killThreads = False

    def get_username(self):
        """
        Gets user input, communicates it with the server
        and the server responds if the username is valid.
        If the username is valid continue with the next function,
        otherwise repeat the function.
        """

        while True:
            clear_screen()

            response = ''
            text_1 = f'\n {Fore.YELLOW}[{Style.RESET_ALL}{Fore.RED}+{Style.RESET_ALL}{Fore.YELLOW}]'
            text_2 = f'{Style.RESET_ALL} Type your username here: {Fore.YELLOW}'

            username = input(text_1 + text_2)
            print(f'{Style.RESET_ALL}')

            if username:
                self.send_msg(username, False)
                response = my_socket.recv(15).decode("utf-8")

            if response == "ACCEPTED":
                self.username = username
                break

            elif response == "DENIED":
                clear_screen()
                print(f'\n [{Fore.RED}+{Style.RESET_ALL}] The username is {Fore.RED}reserved/used{Style.RESET_ALL}')
                input(f' [{Fore.RED}+{Style.RESET_ALL}] Press enter to {Fore.RED}try again!{Style.RESET_ALL} ')

    def receive_msg(self):
        """
        The main thread resides here, we put the main thread to loop for ever
        until the connection with the server is closed, the way we receive messages
        is using HEADERS, we include a header in each message we want to send that
        includes the size of the message the header size (10) and the actual message
        The message looks like this: 54.........Whats up buddy, long time no see.
        The dots are the header size(10) so we can send and receive data up to 10.000.000.000 characters long.
        """

        new_msg = True
        full_msg = ''
        msg_size = 0

        while True:
            try:
                msg = my_socket.recv(HEADER_SIZE).decode("utf-8")

                if new_msg:
                    msg_size = int(msg[:HEADER_SIZE])
                    new_msg = False

                full_msg += msg

                if len(full_msg) - HEADER_SIZE == msg_size:

                    if '[+] SERVER -->' in full_msg:
                        print('\n ')
                        sound_thread = threading.Thread(target=self.sound_left)
                        sound_thread.start()

                    elif 'URL:' in full_msg:
                        try:
                            my_msg = full_msg[HEADER_SIZE:]
                            my_msg = my_msg.split(' ', 1)[1]
                            my_msg = my_msg.split(':', 1)[1]
                            self.open_url(my_msg)
                        except:
                            self.messages.append('Server: Invalid URL format')

                    else:
                        sound_thread = threading.Thread(target=self.sound_message)
                        sound_thread.start()

                    self.store_msg(full_msg)
                    self.msg_printer()
                    full_msg = ''
                    new_msg = True

            except ConnectionResetError:
                break

        self.killThreads = True
        return True

    def send_msg(self, msg, store=True):
        """
         Here we receive an argument msg and store, if store is not provided on
         the method call then it defaults as True, we take the message we want to send
         we add the size of the message, we add the header size and the message and we
         send it to the server.
         Every time we receive, send a message we call the msg_printer method to update
         our screen.
        """

        try:
            msg = f'{len(msg):<{HEADER_SIZE}}' + msg

            if store:
                self.store_msg(msg)

            msg = msg.encode("utf-8")
            my_socket.send(msg)
            self.msg_printer()

        except ConnectionResetError:
            pass

    def store_msg(self, msg):
        """
        This method appends the msg from HEADER_SIZE till the end
        so if the message is: 5..........Hello
        then msg[HEADER_SIZE:] is equal to Hello
        """

        self.messages.append(msg[HEADER_SIZE:])

    def recv_spec(self):
        """
        This method is very similar to the recv_msg method
        but instead of receiving normal messages ("utf-8")
        it receives bytes, the communication between this method
        and the server is done on a different socket instead of using
        the recv_msg socket, communicating multiple messages with the same socket connection
        can lead to errors, messages get concatenated.
        """

        new_msg = True
        full_msg = b''
        msg_size = 0

        while True:
            try:
                msg = command.recv(HEADER_SIZE)

                if new_msg:
                    msg_size = int(msg[:HEADER_SIZE])
                    new_msg = False

                full_msg += msg

                if len(full_msg) - HEADER_SIZE == msg_size:
                    self.users_online = pickle.loads(full_msg[HEADER_SIZE:])
                    self.msg_printer()
                    full_msg = b''
                    new_msg = True

            except ConnectionResetError:
                break

        return True

    def sound_message(self):
        playsound('message.wav')

    def sound_left(self):
        playsound('exit.wav')

    def open_url(self, link):
        try:
            webbrowser.open_new(link)
        except Exception as error:
            print(error)
            self.messages.append('SERVER: Invalid URL')

    def run_threads(self):
        """
        The main thread comes here, creates threads and
        starts them.
        """

        get_inp = threading.Thread(target=self.get_input)
        cmd = threading.Thread(target=self.recv_spec)
        get_inp.start()
        cmd.start()

        if get_inp and cmd:
            return True

    def msg_printer(self):
        """
        On this method we print two lists, users_online and
        messages, the outcome of this method is our screen
        with our messages and showing the users that are online.
        """

        clear_screen()
        print('\n')

        for user in self.users_online:
            text_1 = f' {Fore.YELLOW}[{Style.RESET_ALL}{Fore.RED}+{Style.RESET_ALL}'
            text_2 = f'{Fore.YELLOW}]{Style.RESET_ALL} {Fore.WHITE}{user}{Style.RESET_ALL} '
            print(text_1 + text_2)

        print(f' {Fore.YELLOW}{20 * "-"}{Style.RESET_ALL}\n\n')
        print(" Type URL: and paste a link to open on your friends browser")
        print(" Example --> URL:facebook.com\n\n")

        for message in self.messages:

            if '[+] SERVER -->' in message:
                print('\n' + message + '\n')
            else:
                index = message.index(':')
                text_1 = f'  {Back.RED}{Fore.WHITE}{" " + message[0:index+1]}{Style.RESET_ALL}'
                text_2 = f' {message[index+1:]}'
                print(text_1 + text_2)


    def get_input(self):
        """
        Here we get the input from the user, if the user press
        enter without typing anything then our screen will refresh,
        otherwise we will send the message to the server.
        """

        while True:
            msg = input(f'\n {self.username}: {Fore.GREEN}')
            print(f'{Style.RESET_ALL}')

            if self.killThreads:
                break

            elif msg:
                self.send_msg(f'{self.username}: ' + msg)

            else:
                self.msg_printer()

        return True


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


while True:
    try:
        #'86.5.86.182'
        my_ip = socket.gethostname()
        my_socket.connect((my_ip, PORT))
        command.connect((my_ip, CMD_PORT))
        encrypt.connect((my_ip, ENCR_PORT))

        animation = 0
        server_chat = Chat()
        server_chat.get_username()

        killThread_1 = server_chat.run_threads()
        killThread_2 = server_chat.receive_msg()

        # When we kill a thread or it dies on its own it returns True,
        # if both our receive thread and the two threads running on the
        # run_threads method return True then we know that all threads
        # are dead and we can safely close our program.

        if killThread_1 and killThread_2:
            input(f' [{Fore.RED}+{Style.RESET_ALL}] The server is closed > ')
            break

    except WindowsError:
        # We get WindowsError only when the server is closed or unreachable
        while True:
            clear_screen()

            if animation > 3:
                animation = 0

            text_1 = f'\n [{Fore.RED}+{Style.RESET_ALL}] attempting to '
            text_2 = f'join the server{Fore.BLUE}{animation * "."}{Style.RESET_ALL}'
            print(text_1 + text_2)
            animation += 1
