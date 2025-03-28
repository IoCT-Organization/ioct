
import socket
import json

def receive_data():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 12345))
    sock.listen(1)
    while True:
        conn, addr = sock.accept()
        data = conn.recv(1024).decode()
        conn.close()
        return json.loads(data)

if __name__ == "__main__":
    while True:
        data = receive_data()
        print(f"Received: {data}")