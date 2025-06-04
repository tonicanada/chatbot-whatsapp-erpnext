import os
import sys
import pandas as pd

# Agregar la raíz del proyecto al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importar queries en archivo db/queries.py
import db.queries as sql

# Importa la función para conectarse a la db que está en config/database.py
from config.database import get_db_connection

from utils.google_services_auth import authenticate_with_service_account
from utils.google_sheet_utils import create_google_sheet, write_to_sheet



def resumen_profit_loss_por_grupo_obras_google(fecha_inicio, fecha_fin, empresa, filtro_obras, time_unit, folder_id):
    """
    Genera un reporte de Profit & Loss en un Google Sheet para obras seleccionadas según `filtro_obras`.
    Crea múltiples pestañas similares a las del Excel.
    """
    
    try:
        db = get_db_connection(empresa)
        sheets_service, drive_service = authenticate_with_service_account()
        
        # Crear Google Sheet
        sheet_id = create_google_sheet(sheets_service, drive_service, title="Reporte Profit & Loss", folder_id=folder_id)
        if not sheet_id:
            print("Error al crear Google Sheet")
            return
        
        # Cargar datos
        df = pd.read_sql(sql.query_ploss_por_obra_cuentacontable_centrocoste_year(fecha_inicio, fecha_fin), con=db)
        df_timeunit_cuentacontable = pd.read_sql(sql.query_ploss_por_obra_cuentacontable_year(fecha_inicio, fecha_fin), con=db)
        df_timeunit_costcenter = pd.read_sql(sql.query_ploss_por_obra_centrocoste_year(fecha_inicio, fecha_fin), con=db)
        
        unidades_tiempo = df[time_unit].sort_values().unique()
        
        def guardar_pivot_google(df_pivot, sheet_name):
            """Guarda un DataFrame pivotado en una hoja de Google Sheets."""
            values = [df_pivot.columns.insert(0, "") .tolist()] + df_pivot.reset_index().values.tolist()
            write_to_sheet(sheets_service, sheet_id, sheet_name, "A1", values)
        
        # Resumen por centro de costos y cuenta contable
        for df_data, index_col, sheet_name in [
            (df_timeunit_costcenter, "obra", "resumen_costcenter"),
            (df_timeunit_cuentacontable, "cuenta", "resumen_cuentacontable")
        ]:
            df_filtrado = df_data[df_data.obra.str.match(filtro_obras)]
            df_pivot = df_filtrado.pivot_table(values="saldo", index=index_col, columns=time_unit, aggfunc="sum").fillna(0)
            guardar_pivot_google(df_pivot, sheet_name)
        
        # Reportes por unidad de tiempo
        for unidad in unidades_tiempo:
            df_filtrado = df[(df[time_unit] == unidad) & df.obra.str.match(filtro_obras)]
            if not df_filtrado.empty:
                df_filtrado = df_filtrado.drop(columns=["year"], errors="ignore")
                df_pivot = df_filtrado.pivot_table(values="saldo", index="cuenta", columns="obra", aggfunc="sum").fillna(0)
                df_pivot = df_pivot[df_pivot.sum().sort_values(ascending=False).index]
                guardar_pivot_google(df_pivot, str(unidad))
        
        url_reporte = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        print(f"✅ Reporte generado: {url_reporte}")
        return sheet_id
    
    except Exception as e:
        print(f"Error al generar reporte: {e}")
        return False
            
    
    
# resumen_profit_loss_por_grupo_obras_google("2024-01-01", "2024-12-31", "te", ".*", "year", "15XET6Tu61pyZPjSs_wwGIvayKDaW-4G_")
    