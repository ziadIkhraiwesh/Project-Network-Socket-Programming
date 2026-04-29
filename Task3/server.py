import socket
import threading
import random
import time

# Game parameters
tcp_port = 6000
udp_port = 6001
server_name = 'localhost'
min_players = 2
max_players = 4
to_enter_your_guess = 10  # seconds to enter each guess
game_duration = 60  # total game duration in seconds

# Global variables
players = {}  # client_socket: player_name
guesses = {}  # player_name: guess
guess_counts = {}
game_active = False
number_to_guess = None
lock = threading.Lock()

def broadcast(message):
    for client_socket in list(players.keys()):
        try:
            client_socket.sendall(message.encode('utf-8'))
        except:
            # Handle broken connections
            client_socket.close()
            with lock:
                if client_socket in players:
                    del players[client_socket]

def update_waiting_room():
    with lock:
        player_names = '\n'.join(players.values())
        message = f"Waiting Room:\n{player_names}\n"
        for client_socket in players:
            try:
                client_socket.sendall(message.encode('utf-8'))
            except:
                client_socket.close()


def handle_client(client_socket, addr):
    global game_active
    global number_to_guess
    try:
        # Ask client for their name
        client_socket.sendall("Please enter your name: ".encode('utf-8'))
        name = client_socket.recv(1024).decode('utf-8').strip()

        if not name:
            client_socket.sendall("Invalid name, disconnecting...\n".encode('utf-8'))
            client_socket.close()
            return

        with lock:
            players[client_socket] = name

        print(f"[NEW CONNECTION] {name} connected from {addr}")
        client_socket.sendall(f"Connected as {name}\n".encode('utf-8'))
        client_socket.sendall(f"UDP connection established\n\n".encode('utf-8'))
        update_waiting_room()

        # Wait for the game to start
        while not game_active:
            time.sleep(1)

        player_list = ', '.join(players.values())
        client_socket.sendall(f"Game started with players: {player_list}.\n".encode('utf-8'))
        client_socket.sendall(f"You have {game_duration} seconds to guess the number (1-100)!\n".encode('utf-8'))

        while game_active:
            client_socket.sendall("Enter your guess (1-100): \n".encode('utf-8'))
            client_socket.settimeout(to_enter_your_guess)
            try:
                guess_msg = client_socket.recv(1024).decode('utf-8').strip()
                if not guess_msg:
                    break
                if guess_msg.lower() == 'exit':
                    client_socket.sendall("You have left the game.\n".encode('utf-8'))
                    break
                if not guess_msg.isdigit():
                    client_socket.sendall("Please enter a valid number.\n".encode('utf-8'))
                    continue

                guess_num = int(guess_msg)

                if guess_num < 1 or guess_num > 100:
                    client_socket.sendall("WARNING: Out of range, you missed your chance.\n".encode('utf-8'))
                    continue
                elif guess_num < number_to_guess:
                    client_socket.sendall("Feedback: LOWER!\n".encode('utf-8'))
                elif guess_num > number_to_guess:
                    client_socket.sendall("Feedback: HIGHER!\n".encode('utf-8'))
                else:
                    client_socket.sendall("Feedback: CORRECT!\n".encode('utf-8'))
                    with lock:
                        guesses[name] = guess_num
                        game_active = False
                        winner_message = f"=== GAME RESULTS ===\nTarget number was: {number_to_guess}\nWinner: {name}\n"
                        broadcast(winner_message)
                        print(f"Game Completed. Winner: {name}")
                        guesses.clear()
                        players.clear()
                    break

            except Exception:
                break

    except Exception as ex:
        print(f"Connection error with client {addr}: {ex}")

    finally:
        with lock:
            if client_socket in players:
                print(f"[DISCONNECT] {players[client_socket]} disconnected.")
                name = players[client_socket]  # Save the name before removing
                del players[client_socket]

                # Check remaining players
                if game_active and len(players) == 1:
                    winner = list(players.values())[0]  # Get the remaining player's name
                    winner_message = f"=== GAME RESULTS ===\nTarget number was: {number_to_guess}\nWinner: {winner}\n"
                    broadcast(winner_message)
                    print(f"Game Completed. Winner: {winner}")
                    game_active = False  # End game

            if name in guesses:
                guesses.pop(name, None)
        client_socket.close()


def start_game():
    global game_active, number_to_guess
    with lock:
        number_to_guess = random.randint(1, 100)
        num_players = len(players)
    print(f"Starting game with {num_players} players.\n")
    start_time = time.time()

    while game_active and (time.time() - start_time) < game_duration:
        time.sleep(1)

    with lock:
        if game_active:
            winners = [name for name, guess in guesses.items() if guess == number_to_guess]
            if winners:
                message = f"=== GAME RESULTS ===\nTarget number was: {number_to_guess}\nWinners: {', '.join(winners)}\n"
            else:
                message = "Game Over! No winners this time.\n"
            broadcast(message)
            print(message)
        game_active = False

def start_server():
    global game_active
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_name, tcp_port))
    server.listen(max_players)
    print(f"Server started on <{server_name}>: TCP {tcp_port}, UDP {udp_port}\n")
    threading.Thread(target=wait_for_minimum_players_and_start_game, daemon=True).start()

    while True:
        try:
            client_socket, addr = server.accept()
            with lock:
                if len(players) >= max_players:
                    client_socket.sendall("Server full. Try again later.\n".encode('utf-8'))
                    client_socket.close()
                    continue
            threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
        except Exception as e:
            print(f"Error accepting connections: {e}")

def wait_for_minimum_players_and_start_game():
    global game_active
    while True:
        time.sleep(1)
        with lock:
            player_count = len(players)
        if player_count >= min_players and not game_active:
            game_active = True
            start_game()

if __name__ == "__main__":
    start_server()
