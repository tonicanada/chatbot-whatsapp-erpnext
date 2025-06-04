import time
import os
from openai import OpenAI
import requests
import socketio
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()


# Configuración
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
URL_EXECUTOR_SERVICE = os.getenv("URL_EXECUTOR_SERVICE")
# sio = socketio.Client()

port = int(os.environ.get("PORT", 8502))

app = Flask(__name__)


def interpretar_solicitud(mensaje):
    """Envía la solicitud a OpenAI y obtiene el JSON con el endpoint e inputs."""
    prompt = f"""Eres un asistente que convierte instrucciones en lenguaje natural en JSON estructurado. 
Tu tarea es identificar el endpoint y los inputs a partir de la solicitud del usuario. 
Solo se permiten tres endpoints, que son los siguientes:
    1. /generate-supplier-payment-transfers
    2. /generate-report-google
    3. /generate-balance-eight-col
    4, /start_task

Reglas generales:
1. Siempre responde únicamente con JSON válido, sin texto adicional.
2. El JSON debe tener dos claves: "endpoint" e "inputs".
3. El valor de "endpoint" debe ser EXACTAMENTE uno de los tres permitidos. Si no puedes determinarlo de forma segura, responde con un JSON de error.
4. Extrae los "inputs" de la solicitud de forma precisa, respetando el formato de los ejemplos.
5. Si la solicitud es ambigua o no se puede mapear a ninguno de los endpoints, responde con:
   {{"error": "No se ha podido determinar el endpoint y los inputs a partir de la solicitud."}}

Ejemplos para generate-supplier-payment-transfers:
- Entrada: "Genera la nómina de pago de proveedores"  
  Salida: {{"endpoint": "/generate-supplier-payment-transfers", "inputs": {{}}}}
- Entrada: "Necesito hacer las transferencias de proveedores"  
  Salida: {{"endpoint": "/generate-supplier-payment-transfers", "inputs": {{}}}}

Ejemplos para generate-report-google:
Nota: Fijar siempre "time_unit" en "year".
- Entrada: "Genera el reporte de resultado contable por obra del 2024 para Constructora Tecton"  
  Salida: {{"endpoint": "/generate-report-google", "inputs": {{"fecha_inicio": "2024-01-01", "fecha_fin": "2024-12-31", "empresa": "ct", "filtro_obras": ".*", "time_unit": "year"}}}}
- Entrada: "Dame el resultado contable por obra del año 2025 para Tecton Edificación"  
  Salida: {{"endpoint": "/generate-report-google", "inputs": {{"fecha_inicio": "2025-01-01", "fecha_fin": "2025-12-31", "empresa": "te", "filtro_obras": ".*", "time_unit": "year"}}}}

Ejemplos para generate-balance-eight-col:
- Entrada: "Dame el balance 8 columnas del año 2025 de Constructora Tecton"  
  Salida: {{"endpoint": "/generate-balance-eight-col", "inputs": {{"fecha_inicio": "2025-01-01", "fecha_fin": "2025-12-31", "empresa": "ct"}}}}
- Entrada: "Necesito el balance 8 columnas de Tecton Edificación para 2023"  
  Salida: {{"endpoint": "/generate-balance-eight-col", "inputs": {{"fecha_inicio": "2023-01-01", "fecha_fin": "2023-12-31", "empresa": "te"}}}}
  
Ejemplos para start_task:
- Entrada: "Ejecutar ejemplo de tarea larga para probar socketio".
  Salida: {{"endpoint": "/start_task", "inputs": {{}}}}

Si la solicitud no se puede mapear claramente a alguno de estos endpoints, responde con:
   {{"error": "No se ha podido determinar el endpoint y los inputs a partir de la solicitud."}}

Ahora procesa: {mensaje}"""

    # Create a client instance
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Use the new chat completions endpoint
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
    )
    # <-- Agregado para debug<e
    print(f"📩 Respuesta cruda de OpenAI: {response}")
    return response.choices[0].message.content


def ejecutar_endpoint(endpoint, inputs):
    """Ejecuta el script llamando a la app Flask."""
    url = f"{URL_EXECUTOR_SERVICE}{endpoint}"
    response = requests.post(url, json=inputs)
    # <-- Agregado para debug
    print(f"📩 Respuesta cruda del servidor ({url}): {response.text}")
    return response.json()


# def ejecutar_socket_endpoint(endpoint, inputs):
#     """Ejecuta el script con WebSocket si es un proceso largo."""
#     print(f"🔌 Intentando conectar a {URL_EXECUTOR_SERVICE} con Socket.IO...")

#     try:
#         @sio.event
#         def connect():
#             """ Maneja la conexión al servidor y se une a la room. """
#             print("✅ Conectado al servidor")
#             sio.emit("join", {"client_id": inputs['client_id']})
        
#         sio.connect(URL_EXECUTOR_SERVICE, transports=['websocket'])
#         print("✅ Conectado exitosamente!")
        
#         @sio.on("status")
#         def on_status(data):
#             """ Recibe actualizaciones de estado. """
#             print(f"📢 [STATUS] {data}")

#         time.sleep(1)  # Esperar antes de emitir
#         print(f"📤 Emitiendo evento {endpoint} con inputs: {inputs}...")
#         sio.emit(endpoint, inputs)

#         # Verificar que se recibe respuesta del servidor
#         @sio.on("resultado")
#         def resultado(data):
#             print(f"✅ Resultado recibido: {data}")
#             sio.disconnect()

#         sio.wait()
#     except Exception as e:
#         print(f"❌ Error en WebSocket: {str(e)}")


@app.route("/chatbot", methods=["POST"])
def chatbot():
    """Recibe el mensaje del usuario y ejecuta el script correspondiente."""
    data = request.json
    mensaje = data.get("mensaje", "")
    client_id = data.get("client_id", "")

    type_endpoints = {
        "/generate-supplier-payment-transfers": {
            "socket": True,
            "client_id": client_id,
            "folder_id": "15XET6Tu61pyZPjSs_wwGIvayKDaW-4G_"
        },
        "/generate-report-google": {
            "socket": False,
            "folder_id": "15XET6Tu61pyZPjSs_wwGIvayKDaW-4G_"
        },
        "/generate-balance-eight-col": {
            "socket": False,
            "folder_id": "15XET6Tu61pyZPjSs_wwGIvayKDaW-4G_"
        },
        "/start_task": {
            "socket": True,
            "client_id": client_id,
        }
    }

    try:
        respuesta = interpretar_solicitud(mensaje)
        respuesta_json = eval(respuesta)  # Convertir string a dict

        if "error" in respuesta_json:
            # No se ejecuta ningún endpoint, se solicita mayor especificidad.
            return jsonify({"error": "Por favor, sea más específico en su solicitud."})

        endpoint = respuesta_json["endpoint"]
        inputs = respuesta_json["inputs"]

        print(respuesta_json)

        if type_endpoints[endpoint]["socket"] == False:
            inputs["folder_id"] = type_endpoints[endpoint]["folder_id"]
            resultado = ejecutar_endpoint(endpoint, inputs)
            return jsonify(resultado)
        elif type_endpoints[endpoint]["socket"] == True:
            # Para endpoints de socket, respondemos con HTTP 202 antes de ejecutar la tarea
            inputs["client_id"] = type_endpoints[endpoint]["client_id"]

            # Enviar una respuesta 202 antes de ejecutar el trabajo largo
            response = jsonify({"message": "Tarea iniciada en segundo plano"})
            response.status_code = 202  # Establecer código de estado HTTP 202
            response_start = response
            ejecutar_endpoint(endpoint, inputs)

            # Responder inmediatamente mientras el trabajo se ejecuta en segundo plano
            return response_start
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port, use_reloader=True)
