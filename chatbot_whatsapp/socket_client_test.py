import socketio

# Este script sirve para conectarse como cliente al servidor socket que establece el "chatbot_executor_service" y revisar si está enviando bien los eventos

URL_EXECUTOR_SERVICE = "http://localhost:5000"

# Aquí se debe poner el número de teléfono que está recibiendo los mensajes de WhatsApp
client_id = "56922223344"

sio = socketio.Client()

@sio.event
def connect():
    """ Maneja la conexión al servidor y se une a la room. """
    print("✅ Conectado al servidor")
    sio.emit("join", {"client_id": client_id})

@sio.event
def disconnect():
    """ Maneja la desconexión del servidor. """
    print("❌ Desconectado del servidor")

@sio.on("status")
def on_status(data):
    """ Recibe actualizaciones de estado. """
    print(f"📢 [STATUS] {data}")

@sio.on("progress")
def on_progress(data):
    """ Recibe actualizaciones de progreso de la tarea. """
    print(f"📊 [PROGRESO] {data['progress']}%")

@sio.on("task_completed")
def on_task_completed(data):
    """ Recibe la notificación cuando la tarea finaliza. """
    print(f"✅ [COMPLETADO] {data}")
    sio.disconnect()

sio.connect(URL_EXECUTOR_SERVICE, transports=["websocket"])
sio.wait()
