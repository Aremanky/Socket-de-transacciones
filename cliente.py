import socket
import json

HOST = '127.0.0.1'
PORT = 11002

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST,PORT))

        login = {"accion": "login", "username": "usuario", "password": "jejegod"}
        s.sendall((json.dumps(login)+ '\n').encode())
        resp = s.recv(1024)
        print(f"[Ciente] Respuesta del servidor: {resp.decode()}")

if __name__ == '__main__':
    main()