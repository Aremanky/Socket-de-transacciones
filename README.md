# Sistema de Transacciones por Sockets

> **Resumen**
>
> Proyecto que implementa un sistema cliente‑servidor para registrar usuarios y procesar transacciones mediante sockets TCP. Está diseñado para mostrar competencias técnicas relevantes para empresas: diseño de protocolo JSON sobre TCP, uso de HMAC y nonces para integridad y protección contra *replay* y *Man-in-the-middle*, gestión de sesiones y concurrencia con hilos, gestión básica de usuarios y registro/monitorización de eventos.

---

## Contenido del repositorio

```
Socket-de-transacciones/
├─ cliente.py
├─ server.py
├─ secure_utils.py
├─ user_manager.py
├─ mitm_attack.py
├─ user.json          
├─ sessions.log
├─ transactions.log
├─ error.log
└─ bloqueados.json    
```

---

## Objetivo

Demostrar un prototipo funcional de un sistema de transacciones sencillo que pone énfasis en:

* Comunicación cliente-servidor por sockets (TCP)
* Protocolo de mensajes en JSON sencillo y extensible
* Integridad de las transacciones mediante HMAC y `nonce`
* Gestión de usuarios (registro, login, bloqueo temporal por intentos fallidos)
* Logs para auditoría y diagnóstico

---

## Tecnologías y dependencias

* Python
* Módulos estándar: `socket`, `threading`, `json`, `hashlib`, `hmac`, `os`, `time`, `datetime`, `getpass`

No se usan dependencias externas; el proyecto es fácil de ejecutar en cualquier entorno con Python instalado.

---

## Diseño del protocolo (resumen)

El cliente y el servidor intercambian mensajes JSON terminados en salto de línea (`\n`). Ejemplos de mensajes:

* Registro

```json
{ "accion": "register", "username": "alice", "password": "secreto" }
```

* Login

```json
{ "accion": "login", "username": "alice", "password": "secreto" }
```

* Solicitar nonce para transacción

```json
{ "accion": "pet_transaccion" }
```

* Enviar transacción con HMAC

```json
{ "accion": "transaccion", "data": "CuentaA,CuentaB,100.0", "mac": "<hmac_hex>" }
```

Respuesta típica del servidor:

```json
{ "status": "OK", "mensaje": "..." }
```

---

## Cómo ejecutar (rápido)

1. Clona o descarga el repositorio.
2. Arranca el servidor:

```bash
python3 server.py
```

3. En otra terminal, ejecuta el cliente (interactivo):

```bash
python3 cliente.py
```

4. Opcional — proxy MITM (para pruebas de integridad/modificación):

```bash
python3 mitm_attack.py
```

**Puertos por defecto**:

* Servidor: `11002`
* Proxy MITM: `11003`

---

## Estructura funcional (qué hace cada archivo)

* `server.py`: servidor multihilo que maneja conexiones, sesiones, generación de nonces, verificación de HMAC, registro de logs y bloqueo temporal de usuarios.
* `cliente.py`: cliente interactivo que permite registrar, iniciar sesión, solicitar nonces y enviar transacciones firmadas.
* `secure_utils.py`: utilidades criptográficas: generación de nonces, cálculo y verificación de HMAC.
* `user_manager.py`: gestor simple de usuarios persistido en `user.json` (hash SHA‑256 de contraseñas, usuarios por defecto).
* `mitm_attack.py`: proxy para pruebas que intercepta y, opcionalmente, modifica transacciones (útil para demostrar detección de ataques de tipo MITM cuando HMAC es correcto/incorrecto).

---

## Logs y auditoría

* `sessions.log`: eventos de login/logout y bloqueos.
* `transactions.log`: transacciones registradas (formato legible).
* `error.log`: errores y alertas relevantes.

Estos ficheros ayudan a auditar el sistema y a depurar durante pruebas.

---

## ¿Qué demuestra este proyecto?

* **Conocimientos de redes**: manejo explícito de sockets y gestión de transferencia de datos en bruto.
* **Diseño de protocolos**: creación de un protocolo JSON simple y razonable para solicitudes y respuestas.
* **Conciencia de seguridad**: uso de HMAC y nonces para integridad; identificación de ataques MITM y replay.
* **Ingeniería del software**: separación de responsabilidades (`user_manager`, `secure_utils`), logging y manejo de errores.
* **Pruebas y validación**: incluye un proxy MITM para comprobar detección de modificaciones — demuestra capacidad para diseñar tests de seguridad.

---

## Licencia

Licencia MIT — libre para uso, revisión y mejora.
