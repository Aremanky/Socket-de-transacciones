import socket
import json
import secure_utils
import hashlib

HOST = '127.0.0.1'
PORT = 11002
passwd = []

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST,PORT))

        print("[Cliente] Conectado al servidor")

        while True:
            accion = input("Acción (1.register/2.login/3.transaccion/4.logout/5.salir): ")
            if accion == "5":
                print("[Cliente] Cerrando conexión...")
                break

            if accion == "1":
                username = input("Nuevo usuario: ")
                password = input("Contraseña: ")
                msg = {"accion": "register", "username": username, "password": password}

            elif accion == "2":
                username = input("Usuario: ")
                password = input("Contraseña: ")
                passwd = []
                passwd.append(password)
                msg = {"accion": "login", "username": username, "password": password}

            elif accion == "3":
                #1º pedimos nonce
                msg = {"accion":"pet_transaccion"}
                s.sendall((json.dumps(msg)+ '\n').encode())
                #2º nos lo envia el servidor
                resp = s.recv(1024).decode()
                resp = json.loads(resp)
                #Vemos si está todo bien
                status = resp.get("status")
                #Si es así, es decir que nos hemos logeado, seguimos
                if status == "OK":
                    #reconocemos el nonce que nos manda el servidor
                    nonce = resp.get("nonce")
                    #creamos el mensaje
                    data = input("Introduce transacción (CuentaOrigen,CuentaDestino,Cantidad): ")
                    #sacamos la contraseña, perdon por ser tan bruto para esto
                    key = passwd[0]
                    #le sacamos el hash porque es lo que tiene el servidor
                    key = hashlib.sha256(key.encode()).hexdigest()
                    #calculamos el hmac
                    mac = secure_utils.calcula_hmac(key,data, nonce)
                    #mandamos petición de transacción
                    msg = {"accion": "transaccion", "data": data, "mac":mac}

            elif accion =="4":
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