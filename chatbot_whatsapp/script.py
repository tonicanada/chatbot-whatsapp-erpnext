import os
import requests
import json
from dotenv import load_dotenv
import time

load_dotenv()




import socketio 
from flask import Flask, request


# Esperar 3 segundos
# time.sleep(3)

# Configuración de Flask
app = Flask(__name__)

# Variables de entorno
whatsapp_token = os.getenv("WHATSAPP_TOKEN")
access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
url_openai_service = os.getenv("URL_OPENAI_SERVICE")
url_executor_service = os.getenv("URL_EXECUTOR_SERVICE")

# Crear cliente Socket.IO
sio = socketio.Client()

# Mapeo de usuario y número de WhatsApp
usuarios_ws = {}





def conectar_socket():
    """Se conecta a WebSocket una sola vez al iniciar la aplicación."""
    try:
        print("🔄 Conectando al WebSocket...")
        sio.connect(url_executor_service)
        print("✅ Conectado al WebSocket")
    except Exception as e:
        print(f"❌ Error al conectar con WebSocket: {e}")


# Conectar WebSocket al inicio de la aplicación
# eventlet.spawn(conectar_socket)



# Crear sesión global para mejorar el manejo de conexiones HTTP
session = requests.Session()

def enviar_mensaje_whatsapp(numero, mensaje):
    try:
        api_url = "https://graph.facebook.com/v22.0/480723468466786/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {whatsapp_token}"
        }
        body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {"body": mensaje}
        }
        response = session.post(api_url, json=body, headers=headers)  # Usamos session en vez de requests.post()
        if response.status_code == 200:
            print(f"✅ Mensaje enviado a {numero}: {mensaje}")
        else:
            print(f"❌ Error enviando mensaje a {numero}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")



@sio.event
def connect():
    """ Maneja la conexión al servidor y se une a la room. """
    print("✅ Conectado al servidor")


@sio.event
def connect_error(data):
    print(f"❌ Error de conexión: {data}")


@sio.event
def disconnect():
    print("🛑 Desconectado del servidor WebSocket")


@sio.on("status")
def manejar_evento(data):
    numero = data.get("client_id")
    mensaje = data.get("message", "Sin mensaje")

    print(f"🔴 Evento recibido para {numero}: {mensaje}")
    enviar_mensaje_whatsapp(numero, mensaje)


@sio.on("progress")
def on_progress(data):
    """ Recibe actualizaciones de progreso de la tarea. """
    numero = data['client_id']
    mensaje = f"📊 [PROGRESO] {data['progress']}%"
    print(mensaje)
    enviar_mensaje_whatsapp(numero, mensaje)


conectar_socket()

# @sio.on("task_completed")
# def on_task_completed(data):
#     usuario = data.get("usuario")
#     mensaje = data.get("message", "Tarea completada")

#     print(f"✅ [COMPLETADO] {mensaje}")

#     if usuario in usuarios_ws:
#         numero = usuarios_ws[usuario]
#         enviar_mensaje_whatsapp(numero, f"✅ {mensaje}")

#     print("🔌 Cerrando conexión WebSocket...")
#     sio.disconnect()

def formatear_mensaje(data):
    if not isinstance(data, dict):
        return str(data)
    partes = []
    for clave, valor in data.items():
        partes.append(f"{clave}: {valor}")
    return "\n".join(partes)



def procesar_mensaje_whatsapp(usuario, numero, mensaje):
    try:
        response = requests.post(
            f"{url_openai_service}/chatbot", json={"mensaje": mensaje, "client_id": numero})

        if response.status_code == 200:
            data = response.json()
            mensaje_formateado = formatear_mensaje(data)
            enviar_mensaje_whatsapp(numero, mensaje_formateado)
            return json.dumps(data)

        elif response.status_code == 202:
            print(f"🟡 Activando WebSocket para {usuario}...")
            if sio.connected:
                try:
                    sio.emit("join", {"client_id": numero})
                    print(f"🟢 Cliente {numero} se unió a la room")
                except Exception as e:
                    print(f"❌ Error al conectar con WebSocket: {e}")
                    return "Error al conectar con WebSocket"

            # Emitir evento para escuchar mensajes específicos del usuario
            sio.emit("conectar_cliente", {"usuario": usuario})
            return
    except Exception as e:
        import traceback
        print("❌ ERROR NO CONTROLADO:")
        traceback.print_exc()
        return "Error inesperado"


@app.route('/whatsapp', methods=['GET'])
def VerifyToken():
    try:
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        print(challenge)
        print(access_token)

        if token == access_token:
            return challenge
        else:
            return "error", 400
    except:
        return "error", 400


@app.route('/whatsapp', methods=['POST'])
def received_message():
    # try:
    body = request.get_json()
    entry = body.get('entry', [])
    if entry:
        changes = entry[0].get('changes', [])
        if changes:
            value = changes[0].get('value', {})
            messages = value.get('messages')
            if messages:
                message = messages[0]
                number = message.get('from')
                question_user = message.get('text', {}).get('body', '')
                usuario = message.get('from')

                print(f"📩 Mensaje recibido de {number}: {question_user}")

                # Ejecutar procesamiento en background
                # eventlet.spawn(procesar_mensaje_whatsapp, usuario, number, question_user)
                procesar_mensaje_whatsapp(usuario, number, question_user)

            else:
                print("No se encontraron mensajes en el payload.")
        else:
            print("No se encontraron cambios en el payload.")
    else:
        print("No se encontró 'entry' en el payload.")
    return "EVENT_RECEIVED"
    # except Exception as e:
    #     print(f"❌ Error procesando mensaje: {e}")
    #     return "EVENT_RECEIVED"


if __name__ == '__main__':
    import os
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host='0.0.0.0', port=8501, debug=debug_mode)

