import os
import sys
import logging
from flask_socketio import SocketIO
from flask import Blueprint, request, send_file, jsonify
from scripts.balance_8_col import generar_balance_8_columnas
from scripts.pl_costcenter import resumen_profit_loss_por_grupo_obras
from scripts.pl_costcenter_gsheet import resumen_profit_loss_por_grupo_obras_google
from scripts.pago_proveedores import genera_nominas_pago_proveedores_todos_erp

pl_blueprint = Blueprint("pl", __name__)

# Agregar la raíz del proyecto al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # Para asegurarte que se reconfigure aunque haya otra config previa
)



@pl_blueprint.route("/generate-report", methods=["POST"])
def generate_report():
    fecha_inicio = request.json.get("fecha_inicio", "2024-01-01")
    fecha_fin = request.json.get("fecha_fin", "2024-12-31")
    empresa = request.json.get("empresa", "te")
    filtro_obras = request.json.get("filtro_obras", ".*")
    time_unit = request.json.get("time_unit", "year")

    # Generar el reporte
    resumen_profit_loss_por_grupo_obras(fecha_inicio, fecha_fin, empresa, filtro_obras, time_unit)

    file_path = "resultado_obras.xlsx"
    
    if os.path.exists(file_path):
        try:
            # Enviar el archivo al usuario
            response = send_file(file_path, as_attachment=True)
            return response
        finally:
            # Eliminar el archivo después de enviarlo
            os.remove(file_path)
    else:
        return {"error": "El archivo no se generó correctamente"}, 500
  
    

@pl_blueprint.route("/generate-report-google", methods=["POST"])
def generate_report_google():
    """Endpoint para generar un reporte en Google Sheets y devolver la URL."""

    # Obtener parámetros de la solicitud POST con valores por defecto
    data = request.json
    fecha_inicio = data.get("fecha_inicio", "2024-01-01")
    fecha_fin = data.get("fecha_fin", "2024-12-31")
    empresa = data.get("empresa", "te")
    filtro_obras = data.get("filtro_obras", ".*")
    time_unit = data.get("time_unit", "year")
    folder_id = data.get("folder_id")  # Necesario para saber dónde guardar el archivo

    if not folder_id:
        return jsonify({"error": "Se requiere folder_id para almacenar el reporte en Google Drive"}), 400

    # Llamar a la función importada
    sheet_url = resumen_profit_loss_por_grupo_obras_google(fecha_inicio, fecha_fin, empresa, filtro_obras, time_unit, folder_id)

    if sheet_url:
        return jsonify({
            "message": "✅ Reporte generado con éxito",
            "google_sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_url}"
        })
    else:
        return jsonify({"error": "Hubo un problema al generar el reporte"}), 500


@pl_blueprint.route("/generate-balance-eight-col", methods=["POST"])
def generate_balance_eight_col():
    """Endpoint para generar un reporte en Google Sheets y devolver la URL."""
        # Obtener parámetros de la solicitud POST con valores por defecto
    data = request.json
    fecha_inicio = data.get("fecha_inicio", "2024-01-01")
    fecha_fin = data.get("fecha_fin", "2024-12-31")
    empresa = data.get("empresa", "te")
    folder_id = data.get("folder_id")
    
    if not folder_id:
        return jsonify({"error": "Se requiere folder_id para almacenar el reporte en Google Drive"}), 400
    
    # Llamar a la función importada
    sheet_url = generar_balance_8_columnas(fecha_inicio, fecha_fin, empresa, folder_id)
    
    if sheet_url:
        return jsonify({
            "message": "✅ Reporte generado con éxito",
            "google_sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_url}"
        })
    else:
        return jsonify({"error": "Hubo un problema al generar el reporte"}), 500
    

@pl_blueprint.route("/generate-supplier-payment-transfers", methods=["POST"])
def generate_supplier_payment_transfers():
    from app import socketio 
    """Inicia la generación de la nómina de transferencias con feedback en tiempo real."""
    data = request.json
    client_id = data.get("client_id", "default")
    output_folder_id = data.get("folder_id")
    socketio.start_background_task(genera_nominas_pago_proveedores_todos_erp, output_folder_id, client_id)
    return jsonify({"message": "Tarea iniciada", "client_id": client_id})




def long_running_task(client_id):
    from app import socketio
    """Simula una tarea larga enviando actualizaciones de progreso al cliente en su room."""
    for i in range(1, 6):
        socketio.sleep(3)
        progress = i * 20
        print(f"Enviando progreso: {progress} a room {client_id}")  # Agregar log
        logging.info(f"Enviando progreso: {progress} a room {client_id}")
        socketio.emit('progress', {'progress': progress, 'client_id': client_id}, room=client_id)
    socketio.emit("task_completed", {"client_id": client_id, "message": "Proceso finalizado"})    


@pl_blueprint.route('/start_task', methods=['POST'])
def start_task():
    from app import socketio
    """Inicia una tarea larga en segundo plano."""
    data = request.json
    client_id = data.get("client_id", "default")
    
    socketio.start_background_task(long_running_task, client_id)
    
    return jsonify({"message": "Tarea iniciada", "client_id": client_id})