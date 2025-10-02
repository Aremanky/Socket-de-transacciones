import socket
import threading
import json
from user_manager import UserManager
import os
import secure_utils
from datetime import datetime

#Archivos donde guardamos los logs (registrar las acciones del usuario)
SESSIONS_LOG = "sessions.log"
TRANSACTIONS_LOG = "transactions.log"
ERROR_LOG = "error.log"

#Gestor de base de datos
user_manager = UserManager()

#Memorias que vamos a usar
sesiones = {} #addr como clave y usuario como valor. Ejemplo:{(127.0.0.1,63923): "usuario1"}
dic_nonce = {} #diccionario que genera nonce por transacción

HOST = '0.0.0.0' # Interfaz por la que escucha el servidor (0.0.0.0 indica que en todas)
PORT = 11002 # Puerto por el que escucha

#hacemos volatil la memeoria de transacciones
if os.path.exists(TRANSACTIONS_LOG):
    os.remove(TRANSACTIONS_LOG)

# ---Estas son las funciones de log---
def log_session_event(evento: str):
    ahora = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]") # Formato de fecha y hora
    with open(SESSIONS_LOG, "a") as f:
        f.write(ahora + evento + "\n") # Escribimos en el log la hora y el evento

def log_transaction(transaccion: str):
    ahora = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]") # Formato de fecha y hora
    with open(TRANSACTIONS_LOG, "a") as f:
        f.write(ahora + transaccion + "\n") # Escribimos en el log la hora y la transacción

def log_error(error: str):
    ahora = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]") # Formato de fecha y hora
    with open(ERROR_LOG, "a") as f: 
        f.write(ahora + error + "\n") # Escribimos en el log la hora y el error

# ---Manejo de clientes---
def handle_client(conn, addr): 
    # Hilo que maneja la conexión con un cliente concreto el de {addr}
    print(f"[+] Cliente con ip {addr} se ha conectado")
    buffer = ""
    try:
        with conn:
            while True:
                # Recibimos la instrucción del cliente
                data = conn.recv(1024)
                if not data: # Si no hay datos, el cliente se ha desconectado
                    break
                buffer += data.decode()

                # Los mensajes vienen al final con un salto de línea. Si se llega al salto de linea es el fin del mensaje
                while '\n' in buffer:

                    #Procesamos el mensaje uno a uno
                    mensaje, buffer = buffer.split('\n',1)

                    if mensaje.strip():
                        try:
                            #Parseamos el mensaje JSON
                            obj = json.loads(mensaje)
                            print(f"[{addr}] Mensaje de JSON: {obj}")

                            accion = obj.get("accion")

                            # ---Registro de usuario---
                            if accion == "register":
                                ok, msg = user_manager.register_user(obj["username"], obj["password"]) #Registrar usuario
                                resp = {"status": "OK" if ok else "ERROR", "mensaje": msg}
                                if ok:
                                    resp = {"status": "OK", "mensaje":msg}
                                else:
                                    resp = {"status":"ERROR", "mensaje":msg}
                                    log_error(f"[ERROR] por parte de {addr}: {msg}")

                            # ---Login del usuario---
                            elif accion == "login":
                                ok, msg = user_manager.verify_credenciales(obj["username"], obj["password"]) #Verificar si usuario y contraseña son correctos
                                if ok:
                                    sesiones[addr] = obj["username"]
                                    log_session_event(f"[LOGIN] {obj['username']} desde {addr}")
                                resp = {"status": "OK" if ok else "ERROR", "mensaje": msg}
                            
                            #solicitar petición de transacción para generar un nonce
                            elif accion == "pet_transaccion":

                                if addr not in sesiones: #Ver si está logeado
                                    resp = {"status": "ERROR", "mensaje": "Debes iniciar sesión primero"}
                                    log_error(f"[ERROR] por parte de {addr}: No ha iniciado sesion antes de transacción")
                                else:
                                    usuario = sesiones[addr] #Sacamos el usuario para guardar su nonce temporal
                                    nonce = secure_utils.genera_nonce() #Le generamos un nonce
                                    dic_nonce[usuario] = nonce #Guardamos su nonce
                                    resp = {"status": "OK","nonce": nonce} #Devolvemos el nonce al usuario

                            elif accion == "transaccion":
                                transaccion = obj.get("data") #Sacamos la info que envia el usuario
                                # Ejemplo de lo que hay en transaccion: "CuentaOrigen, CuentaDestino, Cantidad"
                                usuario = sesiones[addr] #Usuario que realiza la operación
                                mac = obj.get("mac") #Sacamos el hmac que nos envía el usuario
                                key = user_manager._get_hash_de(usuario) #Sacamos la clave (hash de la contraseña) del usuario
                                nonce = dic_nonce[usuario] #Sacamos nonce dado al usuario

                                #Verificar ataque de replay
                                if not usuario in dic_nonce:
                                    #Si su nonce ya no está en el diccionario, es que ya se ha usado por lo tanto es un posible ataque de replay
                                    resp = {"status": "POSIBLE ATAQUE", "mensaje":"Posible ataque de replay, debe avisar al usuario {usuario}"}
                                    log_error(f"[POSIBLE ATAQUE] al usuario {usuario} por parte de {addr}: Posible ataque de replay, debe avisar al usuario")
                                #Verificar ataque de Man-in-the-middle (evitar cambios)
                                elif not secure_utils.verifica_hmac(mac,key,transaccion,nonce):
                                    #Si el hmac no es correcto, es que el mensaje ha sido modificado por lo tanto es un posible ataque de Man-in-the-middle
                                    resp = {"status": "POSIBLE ATAQUE", "mensaje":"Posible ataque de Man-in-the-middle, debe avisar al usuario {usuario}"}
                                    log_error(f"[POSIBLE ATAQUE] al usuario {usuario} por parte de {addr}: Posible ataque de man-in-the-middle, debe avisar al usuario")
                                else:
                                    dic_nonce.pop(usuario) #Si todo es correcto, eliminamos el nonce para que no se pueda volver a usar
                                    log_transaction(f"[TRANSACCION] {usuario}: {transaccion}") #Guardamos la transacción en el log
                                    resp = {"status": "OK", "mensaje": f"Transferencia registrada: {transaccion}"}

                            # ---Logout del usuario---
                            elif accion == "logout":
                                if addr in sesiones:
                                    usuario = sesiones[addr] #Sacamos el usuario que se va a deslogear
                                    del sesiones[addr] #Eliminamos la sesión
                                    log_session_event(f"[LOGOUT] {usuario} desde {addr}") #Guardamos en el log la acción
                                    resp = {"status": "OK", "mensaje": "Sesión cerrada"}
                                else:
                                    resp = {"status": "ERROR", "mensaje": "No estabas logado"}
                                    log_error(f"[ERROR] intento de desloggeo sin estar logeado") #Guardamos en el log el error

                            conn.sendall((json.dumps(resp) + "\n").encode()) # Enviamos la respuesta al cliente

                        except Exception as e2:
                            print(f"[!] Ha sucedido un error JSON con {addr}: {e2}")
                            log_error(f"[FATAL ERROR] Ha sudecido un error JSON con {addr}: {e2}") #Guardamos en el log el error

    except Exception as e:
        print(f"[!] Ha sucedido un error con {addr}: {e}")
        log_error(f"[FATAL ERROR] Ha sudecido un error con {addr}: {e}") #Guardamos en el log el error
    finally:
        usuario = sesiones.pop(addr, None) #Eliminamos la sesión si existe
        dic_nonce.pop(usuario, None) #Eliminamos el nonce si existe
        if usuario:
            log_session_event(f"[LOGOUT] {usuario} (desconexión inesperada) desde {addr}")  #Guardamos en el log del logout inesperado
        print(f"[-] Cliente con ip {addr} se ha desconectado")

# ---Preparación socket e hilo---
def main():
    #Arranque de servidor y aceptación de conexiones
    #Creamos el socket TCP (AF_INET = IPv4, SOCK_STREAM = TCP)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        # Permitimos reutilizar la dirección/puerto inmediatamente tras cerrar el servidor.
        # Sin esto, al reiniciar rápido puede saltar "Address already in use".
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Asociamos el socket a la dirección IP (HOST) y puerto (PORT) definidos en el programa.
        # Esto "reserva" el puerto para nuestro servidor.
        s.bind((HOST, PORT))

        # Ponemos el socket en modo escucha.
        # El argumento "5" es la cola máxima de conexiones pendientes antes de ser aceptadas.
        s.listen(5)
        print(f"[Servidor] Escuchando en {HOST}:{PORT}")

        # ---Bucle principal de aceptación de conexiones---
        while True:
            # Espera bloqueante hasta que un cliente se conecte.
            # 'conn' es el nuevo socket creado para ese cliente.
            # 'addr' es una tupla con (IP, puerto) del cliente.
            conn, addr = s.accept()

            # Creamos un hilo independiente para manejar a cada cliente.
            # - target=handle_client → función que atenderá al cliente.
            # - args=(conn, addr) → parámetros pasados a la función.
            # - daemon=True → el hilo se cerrará automáticamente si el programa principal termina.
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)

            # Arrancamos el hilo: ahora el cliente es atendido en paralelo.
            t.start()

if __name__ == '__main__':
    main()