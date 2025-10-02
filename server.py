import socket
import threading
import json
from user_manager import UserManager
import os
import secure_utils
from datetime import datetime

SESSIONS_LOG = "sessions.log"
TRANSACTIONS_LOG = "transactions.log"
ERROR_LOG = "error.log"

user_manager = UserManager()
sesiones = {}
transacciones = []
dic_nonce = {} #diccionario que genera nonce por transacción

HOST = '0.0.0.0'
PORT = 11002

if os.path.exists(TRANSACTIONS_LOG):
    os.remove(TRANSACTIONS_LOG)

def log_session_event(evento: str):
    ahora = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(SESSIONS_LOG, "a") as f:
        f.write(ahora + evento + "\n")

def log_transaction(transaccion: str):
    ahora = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(TRANSACTIONS_LOG, "a") as f:
        f.write(ahora + transaccion + "\n")

def log_error(error: str):
    ahora = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(ERROR_LOG, "a") as f:
        f.write(ahora + error + "\n")

def handle_client(conn, addr):
    print(f"[+] Cliente con ip {addr} se ha conectado")
    buffer = ""
    try:
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data.decode()

                while '\n' in buffer:

                    mensaje, buffer = buffer.split('\n',1)

                    if mensaje.strip():
                        try:
                            obj = json.loads(mensaje)
                            print(f"[{addr}] Mensaje de JSON: {obj}")

                            accion = obj.get("accion")

                            if accion == "register":
                                ok, msg = user_manager.register_user(obj["username"], obj["password"])
                                resp = {"status": "OK" if ok else "ERROR", "mensaje": msg}
                                if ok:
                                    resp = {"status": "OK", "mensaje":msg}
                                else:
                                    resp = {"status":"ERROR", "mensaje":msg}
                                    log_error(f"[ERROR] por parte de {addr}: {msg}")

                            elif accion == "login":
                                ok, msg = user_manager.verify_credenciales(obj["username"], obj["password"])
                                if ok:
                                    sesiones[addr] = obj["username"]
                                    log_session_event(f"[LOGIN] {obj['username']} desde {addr}")
                                resp = {"status": "OK" if ok else "ERROR", "mensaje": msg}
                            
                            #solicitar petición de transacción para generar un nonce
                            elif accion == "pet_transaccion":
                                if addr not in sesiones:
                                    resp = {"status": "ERROR", "mensaje": "Debes iniciar sesión primero"}
                                    log_error(f"[ERROR] por parte de {addr}: No ha iniciado sesion antes de transacción")
                                else:
                                    usuario = sesiones[addr] #Sacamos el usuario para guardar su nonce temporal
                                    nonce = secure_utils.genera_nonce() #Le generamos un nonce
                                    dic_nonce[usuario] = nonce #Guardamos su nonce
                                    resp = {"status": "OK","nonce": nonce}

                            elif accion == "transaccion":
                                transaccion = obj.get("data") #Sacamos la info que envia el usuario
                                # Ejemplo de lo que hay en transaccion: "CuentaOrigen, CuentaDestino, Cantidad"
                                usuario = sesiones[addr] #Usuario que realiza la operación
                                mac = obj.get("mac")
                                key = user_manager._get_hash_de(usuario)
                                nonce = dic_nonce[usuario] #Sacamos nonce dado al usuario

                                #Verificar ataque de replay
                                if not usuario in dic_nonce:
                                    resp = {"status": "POSIBLE ATAQUE", "mensaje":"Posible ataque de replay, debe avisar al usuario {usuario}"}
                                    log_error(f"[POSIBLE ATAQUE] al usuario {usuario} por parte de {addr}: Posible ataque de replay, debe avisar al usuario")
                                #Verificar ataque de Man-in-the-middle (evitar cambios)
                                elif not secure_utils.verifica_hmac(mac,key,transaccion,nonce):
                                    resp = {"status": "POSIBLE ATAQUE", "mensaje":"Posible ataque de Man-in-the-middle, debe avisar al usuario {usuario}"}
                                    log_error(f"[POSIBLE ATAQUE] al usuario {usuario} por parte de {addr}: Posible ataque de man-in-the-middle, debe avisar al usuario")
                                else:
                                    dic_nonce.pop(usuario)
                                    transacciones.append({"usuario": usuario, "transaccion": transaccion})
                                    log_transaction(f"[TRANSACCION] {usuario}: {transaccion}")
                                    resp = {"status": "OK", "mensaje": f"Transferencia registrada: {transaccion}"}

                            elif accion == "logout":
                                if addr in sesiones:
                                    usuario = sesiones[addr]
                                    del sesiones[addr]
                                    log_session_event(f"[LOGOUT] {usuario} desde {addr}")
                                    resp = {"status": "OK", "mensaje": "Sesión cerrada"}
                                else:
                                    resp = {"status": "ERROR", "mensaje": "No estabas logado"}
                                    log_error(f"[ERROR] intento de desloggeo sin estar logeado")

                            conn.sendall((json.dumps(resp) + "\n").encode())

                        except Exception as e2:
                            print(f"[!] Ha sucedido un error JSON con {addr}: {e2}")
                            log_error(f"[FATAL ERROR] Ha sudecido un error JSON con {addr}: {e2}")

    except Exception as e:
        print(f"[!] Ha sucedido un error con {addr}: {e}")
        log_error(f"[FATAL ERROR] Ha sudecido un error con {addr}: {e}")
    finally:
        usuario = sesiones.pop(addr, None)
        if usuario:
            log_session_event(f"[LOGOUT] {usuario} (desconexión inesperada) desde {addr}") 
        print(f"[-] Cliente con ip {addr} se ha desconectado")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"[Servidor] Escuchando en {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()

if __name__ == '__main__':
    main()