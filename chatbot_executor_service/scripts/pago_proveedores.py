import os
import sys
import json
import uuid
import requests
import tempfile
import pandas as pd
from pathlib import Path
from datetime import datetime

# Agregar la raíz del proyecto al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Cargar JSON correctamente
datos_empresas = json.loads(Path("./config/credentials/datos_empresas.json").read_text())

from utils.google_services_auth import authenticate_with_service_account
from utils.googls_drive_utils import download_and_save_file_from_drive, upload_file_to_drive


def get_df_from_erpnext_endpoint(endpoint, token, limit_page_length=5000, params=None):
    """
    Obtiene datos paginados desde un endpoint de ERPNext y los devuelve en un DataFrame.

    :param endpoint: URL del endpoint de ERPNext.
    :param token: Diccionario con 'apikey' y 'apisecret'.
    :param limit_page_length: Cantidad de registros por página (por defecto 5000).
    :param params: Parámetros adicionales para la consulta.
    :return: DataFrame con los datos obtenidos del endpoint.
    """
    headers = {
        "Authorization": f"token {token['apikey']}:{token['apisecret']}"
    }

    if params is None:
        params = {}

    params["limit_page_length"] = str(limit_page_length)
    params["limit_start"] = 0  # Inicializa la paginación

    all_data = []

    while True:
        # print(f"Fetching from start {params['limit_start']}...")  # Debugging info
        response = requests.get(endpoint, headers=headers, params=params)
        json_response = response.json()

        if "data" not in json_response:
            print("Error en la respuesta:", json_response)
            break

        data = json_response["data"]
        if not data:
            break  # No hay más datos, terminamos la paginación

        all_data.extend(data)

        # Mover el inicio a la siguiente página
        params["limit_start"] += int(params["limit_page_length"])

    # Convertir los datos a DataFrame
    return pd.json_normalize(all_data)



# CONSULTA API al ERPNext por las facturas pendientes de pago
def get_pinv_unpaid(rut_empresa):
    base_url = datos_empresas[rut_empresa]["erp_url"]
    endpoint = f"{base_url}/api/resource/Purchase Invoice"
    token = {
        "apikey": datos_empresas[rut_empresa]["erp_apikey"],
        "apisecret": datos_empresas[rut_empresa]["erp_apisecret"]
    }
    
    params = {
        "filters": '[["docstatus","=","1"],["outstanding_amount","!=","0"]]',
        "fields": '["name", "supplier", "rut", "bill_no", "bill_date", "due_date", "net_total", "outstanding_amount", "cesion_factoring"]'
    }

    df = get_df_from_erpnext_endpoint(endpoint, token, params=params)

    # Procesamiento adicional
    df["rut"] = df["rut"].str.lower()
    df.insert(0, 'rut_folio', df["rut"] + " FC " + df["bill_no"])
    df["rut_folio"] = df["rut_folio"].str.lower()
    df["due_date"] = pd.to_datetime(df["due_date"])
    df["bill_date"] = pd.to_datetime(df["bill_date"])
    df["dias_de_mora"] = (pd.to_datetime("now") - df["due_date"]).dt.days

    return df



def genera_nomina_transferencias_formato_bci(rut_empresa, output_folder_id):
    try:
    
        # Se baja el archivo que contiene los datos de transferencia de los proveedores
        # Generar un nombre único con UUID
        db_cuentas_filename = f"cuentas_proveedores_{uuid.uuid4().hex}.xlsx"
            
        _, drive_service = authenticate_with_service_account()
        db_cuentas_proveedores = download_and_save_file_from_drive(drive_service, "1z2gDQ2RWxAombgUDqFKGAIO4BJzRL2zc", custom_filename=db_cuentas_filename)
        df_cuentas = pd.read_excel(db_cuentas_proveedores)
        df_cuentas["rut"] = (
            df_cuentas["Rut Beneficiario"].astype(int).astype(str)
            + "-"
            + df_cuentas["Dig. Verif. Beneficiario"].astype(str).str.lower()
        )
        df_cuentas = df_cuentas.drop_duplicates(subset=["rut"], keep="last")
        df_cuentas.drop_duplicates(subset=["rut"], keep="last", inplace=True)
        
        # Se obtienen las facturas pendientes de pago para la empresa seleccionada
        df_pinv_unpaid = get_pinv_unpaid(rut_empresa)
        
        # Si no hay facturas pendientes, se retorna None
        if df_pinv_unpaid.empty:
            return None
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_output_file:
            filename = temp_output_file.name
        
        # Las facturas que están factorizadas deben pagarse a los factorings
        # Se debe cambiar el RUT de pago para esos casos
        
        # Necesitamos poder relacionar los nombres de los factorings con sus RUT
        base_url = datos_empresas[rut_empresa]["erp_url"]
        token = {
            "apikey": datos_empresas[rut_empresa]["erp_apikey"],
            "apisecret": datos_empresas[rut_empresa]["erp_apisecret"]
        }
        params = {
            "fields": '["name", "rut"]'
        }
        suppliername_rut_df = get_df_from_erpnext_endpoint(f"{base_url}/api/resource/Supplier", token, params=params)
        suppliername_rut_df['rut'] = suppliername_rut_df['rut'].str.lower()
        suppliername_rut_df.set_index('name', inplace=True)
        suppliername_rut_dict = suppliername_rut_df['rut'].to_dict()
        
        def completa_rut_factoring_por_fila(row):
            factoring = row['cesion_factoring']
            if factoring is not None:
                return suppliername_rut_dict.get(factoring, None)
            return None
            
        df_pinv_unpaid['rut_factoring'] = df_pinv_unpaid.apply(lambda row: completa_rut_factoring_por_fila(row), axis=1).str.lower()

        # En el caso que la columna rut_factoring no sea None, sustituimos el rut por rut_factoring
        df_pinv_unpaid.loc[pd.notna(df_pinv_unpaid["cesion_factoring"]), "rut"] = df_pinv_unpaid["rut_factoring"]
        
        # Unimos el df_pinv_unpaid para que cada fila contenga los datos para transferir
        df_pinv_unpaid = df_pinv_unpaid.merge(df_cuentas, how="left", on="rut").fillna("")
        df_pinv_unpaid["Monto Transferencia"] = df_pinv_unpaid["outstanding_amount"]
        df_pinv_unpaid["Mensaje Destinatario (3)"] = df_pinv_unpaid["name"] + " " + "FC " + df_pinv_unpaid["bill_no"]
        
        df_pinv_unpaid.loc[df_pinv_unpaid["cesion_factoring"] != "", "Nombre Beneficiario"] = (
            df_pinv_unpaid["supplier"] + " // " + df_pinv_unpaid["cesion_factoring"]
        )
        
        # razon_social_abrev = datos_empresas[rut_empresa]['razon_social_abrev']
        # filename = f'{str(date.today()).replace("-", "")}_{rut_empresa}_{razon_social_abrev}.xlsx'
        # Generar un nombre de archivo único con fecha, RUT y abreviatura
        razon_social_abrev = datos_empresas[rut_empresa]["razon_social_abrev"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Formato AAAAMMDD_HHMMSS
        unique_id = uuid.uuid4().hex[:8]  # 8 caracteres únicos para evitar colisiones
        filename = f"{timestamp}_{rut_empresa}_{razon_social_abrev}_{unique_id}.xlsx"
        
        df_pinv_unpaid.to_excel(filename)

        upload_file_to_drive(drive_service, filename, output_folder_id)
        
    finally:
        # Borra los archivos generados
        if os.path.exists(db_cuentas_filename):
            os.remove(db_cuentas_filename)
        if os.path.exists(filename):
            os.remove(filename)
    
    return df_pinv_unpaid

    
def genera_nominas_pago_proveedores_todos_erp(output_folder_id, client_id):
    from app import socketio

    for rut in datos_empresas:
        try:
            df = genera_nomina_transferencias_formato_bci(rut, output_folder_id)
            if df is not None:
                msg = f"Nómina excel formato BCI generada para empresa {datos_empresas[rut]['razon_social']}, con un total de {len(df)} líneas"
            else:
                msg = f"No hay facturas pendientes de pago para la empresa {datos_empresas[rut]['razon_social']}"

            print(f"📢 Intentando emitir evento 'status': {msg}")  # <-- Agregado para debug
            socketio.emit("status", {"client_id": client_id, "message": msg}, room=client_id)

        except Exception as e:
            msg = f"❌ Error en la nómina {datos_empresas[rut]['razon_social']} (RUT: {rut}): {e}"
            print(msg)
            socketio.emit("status", {"client_id": client_id, "message": msg}, room=client_id)

    # ✅ Emitir evento final de tarea completada
    print(f"✅ Intentando emitir evento 'task_completed' para {client_id}")  # <-- Agregado para debug
    socketio.emit("task_completed", {"client_id": client_id, "message": "Proceso finalizado"})        
    
