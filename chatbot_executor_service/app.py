import eventlet
# Aplicar monkey patching para eventlet
eventlet.monkey_patch()

import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room
from routes.script_routes import pl_blueprint


logging.basicConfig(level=logging.DEBUG)

# Inicia túnel SSH antes de levantar Flask
# start_ssh_tunnel()
# atexit.register(stop_ssh_tunnel)  # Para cerrarlo cuando el servidor muera




app = Flask(__name__)

@app.route("/")
def home():
    return "¡Hola desde devapi.acmsoftware.cl con Docker!"

# Configuración de SocketIO con eventlet
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet", logger=True, engineio_logger=True)

@socketio.on("join")
def on_join(data):
    """ Maneja la unión de un cliente a una room específica. """
    client_id = data.get("client_id")
    if client_id:
        join_room(client_id)
        print(f"👤 Cliente {client_id} se unió a la room.")
        socketio.emit("status", {"message": f"Cliente {client_id} unido a la room"}, room=client_id)
        socketio.emit("progress", {"progress": "Empezando tarea...", "client_id": client_id}, room=client_id)
        socketio.emit("progress", {"progress": "Empezando tarea.. MUY BIEN!!!! .", "client_id": client_id}, room=client_id)


@app.route("/healthcheck")
def healthcheck():
    return "OK", 200

# Registrar el Blueprint en la app
app.register_blueprint(pl_blueprint, url_prefix="/api")


if __name__ == "__main__":
    # Ejecutar servidor socketio
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=True)