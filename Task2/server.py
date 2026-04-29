import socket
import threading
import os

# Function to create response message
def create_response_msg(decoded_msg, addr, client_socket):
    m_type, f_path, _ = decoded_msg.split(" ", 2)
    head = "HTTP/1.1 200 OK \r\n"
    flag = -1
    file = "main_en.html"
    
    # Handling different paths
    if f_path == "/" or f_path == "/en" or f_path == "/index.html" or f_path == "/main_en.html":
        file = "main_en.html"
        flag = 0
    elif f_path == "/mySite_2671_en.html":
        file = "mySite_2671_en.html"
        flag = 0
    elif f_path == "/ar" or f_path == "/main_ar.html":
        file = "main_ar.html"
        flag = 0
    elif f_path.__contains__(".html"):
        file = f_path
        flag = 0
    elif f_path.__contains__(".css"):
        file = f_path.lstrip("/")
        flag = 4
    elif f_path.endswith(".jpg"):
        file = f_path.lstrip("/")
        if not os.path.exists(file):  # Check if the image exists
            flag = 5  # Flag 5 for temporary redirect to Google search
        else:
            flag = 2  # Flag for serving the jpg
    elif f_path.endswith(".png"):
        file = f_path.lstrip("/")
        if not os.path.exists(file):  # Check if the image exists
            flag = 5  # Flag 5 for temporary redirect to Google search
        else:
            flag = 1  # Flag for serving the png
    elif f_path.endswith(".mp4"):
        file = f_path.lstrip("/")
        if not os.path.exists(file):  # Check if the video exists
            flag = 6  # Flag 6 for temporary redirect to YouTube search
        else:
            flag = 3  # Flag for serving the mp4
    else:
        head = "HTTP/1.1 404 Not Found \r\n"
        file = f_path

    # Sending response based on the flag
    if flag == -1:
        client_socket.send("HTTP/1.1 404 Not Found \r\n".encode())
        client_socket.send("Content-Type: text/html; charset=utf-8\r\n".encode())
        client_socket.send("\r\n".encode())
        s = f"""<html><head><title>Error 404</title>
    <style type="text/css">h1 {{font-size: 4em; text-align: center;}}</style>
    </head><body><font color="red"><h1>The file is not found</h1></font>
    <p>Client IP: {addr[0]}</p>
    <p>Client Port: {addr[1]}</p>
    </body></html>"""

        client_socket.send(s.encode())
    elif flag == 0:
        client_socket.send(head.encode())
        client_socket.send("Content-Type: text/html; charset=utf-8\r\n".encode())
        client_socket.send("\r\n".encode())
        with open(file, "rb") as f1:
            client_socket.send(f1.read())
    elif flag == 1:
        client_socket.send(head.encode())
        client_socket.send("Content-Type: image/png\r\n".encode())
        client_socket.send("\r\n".encode())
        with open(file, "rb") as f1:
            client_socket.send(f1.read())
    elif flag == 2:
        client_socket.send(head.encode())
        client_socket.send("Content-Type: image/jpeg\r\n".encode())  # Corrected Content-Type
        client_socket.send("\r\n".encode())
        with open(file, "rb") as f1:
            client_socket.send(f1.read())
    elif flag == 3:
        client_socket.send(head.encode())
        client_socket.send("Content-Type: video/mp4\r\n".encode())
        client_socket.send("\r\n".encode())
        with open(file, "rb") as f1:
            client_socket.send(f1.read())
    elif flag == 4:
        client_socket.send(head.encode())
        client_socket.send("Content-Type: text/css; charset=utf-8\r\n".encode())
        client_socket.send("\r\n".encode())
        with open(file, "rb") as f1:
            client_socket.send(f1.read())
    
    elif flag == 5:  # Temporary Redirect for missing photo (search on Google)
        redirect_url = f"https://www.google.com/search?q={f_path[1:]}"  # Remove the leading "/" from f_path
        print(f"Redirecting to: {redirect_url}")  # Log the redirect URL to ensure it's correct
        client_socket.send("HTTP/1.1 307 Temporary Redirect \r\n".encode())
        client_socket.send(f"Location: {redirect_url}\r\n".encode())  # Set the Location header
        client_socket.send("\r\n".encode())  # End of headers

    elif flag == 6:  # Temporary Redirect for missing video (search on YouTube)
        head = "HTTP/1.1 307 Temporary Redirect  \r\n"
        location = f"Location: https://www.youtube.com/results?search_query={f_path[1:]}\r\n"  # Removing the leading '/'
        print(f"Redirecting to: {location}")  # Log the redirect URL to ensure it's correct
        client_socket.send(head.encode())
        client_socket.send(location.encode())
        client_socket.send("\r\n".encode())

    client_socket.close()




def handle_request(client_socket, addr):
    request_msg = client_socket.recv(1024).decode('utf-8')
    print(f"Request from {addr}: {request_msg}")
    create_response_msg(request_msg, addr, client_socket)  # No return value expected

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip_address = socket.gethostbyname(socket.gethostname())
    port = 9971
    server_socket.bind(("", port))
    server_socket.listen(1)

    print(f"Server started on {host_ip_address}:{port}...")

    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_request, args=(client_socket, addr))
        client_thread.start()

if __name__ == "__main__":
    start_server()
