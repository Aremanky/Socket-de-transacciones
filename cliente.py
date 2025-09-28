import socket
import json

HOST = '127.0.0.1'
PORT = 11002

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST,PORT))

        print("[Cliente] Conectado al servidor")

        while True:
            accion = input("Acción (register/login/transaccion/logout/salir): ")

            if accion == "salir":
                print("[Cliente] Cerrando conexión...")
                break

            if accion == "register":
                username = input("Nuevo usuario: ")
                password = input("Contraseña: ")
                msg = {"accion": "register", "username": username, "password": password}

            elif accion == "login":
                username = input("Usuario: ")
                password = input("Contraseña: ")
                msg = {"accion": "login", "username": username, "password": password}

            elif accion == "transaccion":
                data = input("Introduce transacción (CuentaOrigen,CuentaDestino,Cantidad): ")
                msg = {"accion": "transaccion", "data": data}

            elif accion == "logout":
                msg = {"accion": "logout"}

            else:
                print("Acción no reconocida.")
                continue

            # enviamos el mensaje
            s.sendall((json.dumps(msg)+ '\n').encode())

            # recibimos respuesta
            resp = s.recv(1024)
            print(f"[Cliente] Respuesta del servidor: {resp.decode()}")

if __name__ == '__main__':
    main()