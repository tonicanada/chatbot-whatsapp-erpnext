import os
import sys
import pandas as pd

# Agregar la raíz del proyecto al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importar queries en archivo db/queries.py
import db.queries as sql

# Importa la función para conectarse a la db que está en config/database.py
from config.database import get_db_connection



def resumen_profit_loss_por_grupo_obras(fecha_inicio, fecha_fin, empresa, filtro_obras, time_unit):
    """
    Genera un reporte Excel de Profit & Loss para obras seleccionadas según `filtro_obras`.
    Crea 3 pestañas: obra_año, cuentacontable_año, obra_cuentacontable_año.
    """
    
    db = get_db_connection(empresa)
    
    # Cargar datos
    df = pd.read_sql(sql.query_ploss_por_obra_cuentacontable_centrocoste_year(fecha_inicio, fecha_fin), con=db)
    df_timeunit_cuentacontable = pd.read_sql(sql.query_ploss_por_obra_cuentacontable_year(fecha_inicio, fecha_fin), con=db)
    df_timeunit_costcenter = pd.read_sql(sql.query_ploss_por_obra_centrocoste_year(fecha_inicio, fecha_fin), con=db)

    # Obtener valores únicos
    unidades_tiempo = df[time_unit].sort_values().unique()
    
    # Configurar salida Excel
    writer = pd.ExcelWriter("./resultado_obras.xlsx", engine="xlsxwriter", datetime_format="dd/mm/yyyy")
    workbook = writer.book

    # Formatos
    header_format = workbook.add_format({"bold": True, "valign": "center", "rotation": 90, "fg_color": "#D7E4BC", "border": 1})
    format_numbers = workbook.add_format({"num_format": "#0"})
    index_format = workbook.add_format({"bold": True, "fg_color": "#D7E4BC", "border": 1})
    first_cell_format = workbook.add_format({"bold": True, "fg_color": "#D7E4BC", "border": 1, "valign": "center", "align": "center"})

    def guardar_pivot(df_pivot, sheet_name):
        """Guarda un DataFrame pivotado en una hoja de Excel con formato."""
        df_pivot.to_excel(writer, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        worksheet.set_column("A:A", 60)
        worksheet.set_column("B:ZZ", 5, format_numbers)

    # Generar resumen por centro de costos y cuenta contable
    for df_data, index_col, sheet_name in [
        (df_timeunit_costcenter, "obra", "resumen_costcenter"),
        (df_timeunit_cuentacontable, "cuenta", "resumen_cuentacontable")
    ]:
        df_filtrado = df_data[df_data.obra.str.match(filtro_obras)]
        df_pivot = df_filtrado.pivot_table(values="saldo", index=index_col, columns=time_unit, aggfunc="sum").fillna(0)
        guardar_pivot(df_pivot, sheet_name)

    # Generar reportes por unidad de tiempo (año/mes)
    for unidad in unidades_tiempo:
        df_filtrado = df[(df[time_unit] == unidad) & df.obra.str.match(filtro_obras)]
        if not df_filtrado.empty:
            df_filtrado = df_filtrado.drop(columns=["year"], errors="ignore")
            df_pivot = df_filtrado.pivot_table(values="saldo", index="cuenta", columns="obra", aggfunc="sum").fillna(0)
            df_pivot = df_pivot[df_pivot.sum().sort_values(ascending=False).index]

            guardar_pivot(df_pivot, str(unidad))
            worksheet = writer.sheets[str(unidad)]
            worksheet.set_row(0, 150)
            for col_num, value in enumerate(df_pivot.columns.values):
                worksheet.write(0, col_num + 1, value, header_format)
            for row_num, value in enumerate(df_pivot.index.values):
                worksheet.write(row_num + 1, 0, value, index_format)
            worksheet.write(0, 0, "CUENTA_CONTABLE // OBRA", first_cell_format)

    writer.close()



# resumen_profit_loss_por_grupo_obras("2024-01-01", "2024-12-31", "te", ".*", "year")