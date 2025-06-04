import os
import sys
import locale
import pandas as pd

# Agregar la raíz del proyecto al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importar queries en archivo db/queries.py
import db.queries as sql

# Importa la función para conectarse a la db que está en config/database.py
from config.database import get_db_connection

from utils.google_services_auth import authenticate_with_service_account
from utils.google_sheet_utils import create_google_sheet, write_to_sheet, write_df_to_sheet, delete_sheet


def generar_balance_8_columnas(fecha_inicio, fecha_fin, empresa, folder_id):
    try:
    
        db = get_db_connection(empresa)
        sheets_service, drive_service = authenticate_with_service_account()
        
        # Crear titulo para el reporte sea así (fecha_fin_formateada_yyyy_mm_dd)_(empresa)
        fecha_fin_formateada = pd.to_datetime(fecha_fin).strftime("%Y%m%d")
        title = f"Balance_{empresa}_{fecha_fin_formateada}_"
        
        
        # Crear Google Sheet
        sheet_id = create_google_sheet(sheets_service, drive_service, title=title, folder_id=folder_id)
        if not sheet_id:
            print("Error al crear Google Sheet")
            return
        
        datos_periodo = db.execute(sql.query_balance_8_columnas("2000-01-01", fecha_fin))
        datos_apertura = db.execute(sql.query_balance_8_columnas("2000-01-01", fecha_inicio))
        
        # Convertir los resultados a diccionarios con la estructura deseada
        datos_periodo = {row[0]: (row[1], row[2], row[3], row[4]) for row in datos_periodo}
        datos_apertura = {row[0]: (row[1], row[2], row[3], row[4]) for row in datos_apertura}
        
        
        balance = []
        for cuenta, (tipo_cuenta, debito_total, credito_total, saldo) in datos_periodo.items():
            saldo_apertura = datos_apertura.get(cuenta, [None, 0, 0, 0])[3]
            debito_apertura = datos_apertura.get(cuenta, [None, 0, 0, 0])[1]
            credito_apertura = datos_apertura.get(cuenta, [None, 0, 0, 0])[2]
            
            debito_periodo = debito_total - debito_apertura + (saldo_apertura if saldo_apertura > 0 else 0)
            credito_periodo = credito_total - credito_apertura + (-saldo_apertura if saldo_apertura < 0 else 0)
            
            e = {
                "cuenta": cuenta,
                "debitos": locale.format_string("%.2f", debito_periodo, grouping=False),
                "creditos": locale.format_string("%.2f", credito_periodo, grouping=False),
            }
            
            str_saldo = locale.format_string("%.2f", abs(saldo), grouping=False)
            if saldo >= 0:
                if tipo_cuenta in ["Asset", "Liability", "Equity"]:
                    e.update({"deudor": str_saldo, "activo": str_saldo, "acreedor": 0, "pasivo": 0, "perdida": 0, "ganancia": 0})
                else:
                    e.update({"deudor": str_saldo, "perdida": str_saldo, "acreedor": 0, "activo": 0, "pasivo": 0, "ganancia": 0})
            else:
                if tipo_cuenta in ["Asset", "Liability", "Equity"]:
                    e.update({"deudor": 0, "activo": 0, "perdida": 0, "ganancia": 0, "acreedor": str_saldo, "pasivo": str_saldo})
                else:
                    e.update({"deudor": 0, "activo": 0, "pasivo": 0, "perdida": 0, "acreedor": str_saldo, "ganancia": str_saldo})
            
            balance.append(e)
            
        df = pd.DataFrame(balance)
            
        df["cuenta"] = df["cuenta"].astype(str)
        df.iloc[:, 1:] = df.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
        columnas_ordenadas = ["cuenta", "debitos", "creditos", "deudor", "acreedor", "activo", "pasivo", "perdida", "ganancia"]
        df = df[columnas_ordenadas]
            
            
        # Generar un string que sea: {empresa}: Balance del {fecha_inicio} al {fecha_fin}
        titulo_sheet = f"{empresa.upper()}: Balance del {fecha_inicio} al {fecha_fin}"
        # Escribir en la celda A1 del gsheet el título
        write_to_sheet(sheets_service, sheet_id, "balance8col", "A1", [[titulo_sheet]])
        
        # Escribir el df en la celda "A2"
        write_df_to_sheet(sheets_service, sheet_id, df, "balance8col", "A2")
        
        # Elimina la pestaña "Sheet1" creada por defecto
        delete_sheet(sheets_service, sheet_id, "Sheet1")
        
        
        url_reporte = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        print(f"✅ Reporte generado: {url_reporte}")
        return sheet_id
    
    except Exception as e:
        print(f"Error al generar reporte: {e}")
        return False


# balance = generar_balance_8_columnas("2024-01-01", "2024-12-31", "te", "15XET6Tu61pyZPjSs_wwGIvayKDaW-4G_")
