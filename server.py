import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 11002

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

                            resp = {"status": "OK", "accion": obj.get("accion")}
                            conn.sendall((json.dumps(resp) + "\n").encode())
                        except Exception as e2:
                            print(f"[!] Ha sucedido un error JSON con {addr}: {e2}")

    except Exception as e:
        print(f"[!] Ha sucedido un error con  {addr}: {e}")
    finally:
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