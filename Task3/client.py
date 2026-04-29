import socket
import threading

def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024).decode('utf-8')
            if not msg:
                break
            print(msg, end='')
        except:
            break

def start_client(server_ip='localhost', server_port=6000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))

    # start thread to receive messages
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    # first input is for name prompt
    while True:
        user_input = input()
        if user_input:
            sock.send(user_input.encode('utf-8'))
            break

    # main game input loop
    while True:
        try:
            user_input = input()
            if user_input:
                sock.send(user_input.encode('utf-8'))
                if user_input.lower() == 'exit':
                    break
        except EOFError:
            break

    sock.close()

if __name__ == "__main__":
    start_client()
