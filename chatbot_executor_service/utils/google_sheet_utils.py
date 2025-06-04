import re
from datetime import datetime
from googleapiclient.errors import HttpError

def create_google_sheet(sheets_service, drive_service, title=None, folder_id=None):
    """
    Crea un Google Sheet con un título en una carpeta específica dentro de una unidad compartida.
    
    :param sheets_service: Cliente autenticado de Google Sheets API.
    :param drive_service: Cliente autenticado de Google Drive API.
    :param title: Nombre del archivo (si es None, usa formato YYYYMMDD_HHMMSS_gsheet_example_from_python).
    :param folder_id: ID de la carpeta en la unidad compartida.
    :return: ID del Google Sheet creado o None en caso de error.
    """
    try:
        # Generar título si no se proporciona
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if title is None:
            title = f"{timestamp}_gsheet_example_from_python"
        else:
            title = f"{timestamp}_{title}"

        # Crear el Google Sheet
        spreadsheet = {
            'properties': {'title': title}
        }
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()
        sheet_id = spreadsheet['spreadsheetId']

        # Mover el archivo a la carpeta deseada
        if folder_id:
            file_metadata = drive_service.files().get(fileId=sheet_id, fields="parents").execute()
            previous_parents = ",".join(file_metadata.get("parents", []))

            drive_service.files().update(
                fileId=sheet_id,
                addParents=folder_id,
                removeParents=previous_parents,  # Elimina de la carpeta original (normalmente "My Drive")
                supportsAllDrives=True,
                fields="id, parents"
            ).execute()

        return sheet_id

    except HttpError as error:
        print(f"❌ Error en Google Sheets: {error}")
        return None


def write_to_sheet(sheets_service, sheet_id, sheet_name, range_name, values):
    """Escribe una lista de listas en un Google Sheet en el rango especificado.
       Si la hoja no existe, la crea antes de escribir."""
    try:
        # Obtener todas las hojas del Google Sheet
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_names = [sheet["properties"]["title"] for sheet in spreadsheet["sheets"]]

        # Si la hoja no existe, la creamos
        if sheet_name not in sheet_names:
            requests = [{
                "addSheet": {
                    "properties": {"title": sheet_name}
                }
            }]
            sheets_service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": requests}).execute()
            print(f"✅ Hoja creada: {sheet_name}")

        # Escribir en la hoja (corrección en el formato del rango)
        body = {'values': values}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!{range_name}",  # 🔹 Se corrige el formato del rango
            valueInputOption="RAW",
            body=body
        ).execute()

    except HttpError as error:
        print(f"⚠️ Error al escribir en Google Sheet: {error}")
        
        

def get_range(start_cell, num_rows, num_cols):
    """Calcula el rango de celdas en formato A1:D10 a partir de la celda inicial."""
    
    # Extraer la columna (letras) y la fila (número) desde start_cell
    match = re.match(r"([A-Z]+)(\d+)", start_cell)
    if not match:
        raise ValueError(f"❌ Celda de inicio '{start_cell}' no válida. Usa formato como 'A2'.")

    start_col_letter, start_row = match.groups()
    start_row = int(start_row)  # Convertir fila a número

    # Convertir la letra de columna a un índice (ej: A → 0, B → 1, ..., Z → 25, AA → 26)
    start_col_index = sum((ord(c) - ord('A') + 1) * (26**i) for i, c in enumerate(reversed(start_col_letter))) - 1

    # Calcular la columna final basada en el tamaño del DataFrame
    end_col_index = start_col_index + num_cols - 1

    # Convertir de índice a letra (ej: 0 → A, 25 → Z, 26 → AA)
    def index_to_col(index):
        letters = ""
        while index >= 0:
            letters = chr(index % 26 + ord('A')) + letters
            index = index // 26 - 1
        return letters

    end_col_letter = index_to_col(end_col_index)
    end_row = start_row + num_rows - 1  # 🔹 Corrección: sumamos TODAS las filas del DF

    return f"{start_col_letter}{start_row}:{end_col_letter}{end_row}"



def write_df_to_sheet(sheets_service, sheet_id, df, sheet_name, start_cell="A1"):
    """Escribe un DataFrame en Google Sheets asegurando que se cubra el rango completo desde la celda dada."""

    if df.empty:
        print("⚠️ El DataFrame está vacío. No se escribirá nada en la hoja.")
        return

    values = [df.columns.tolist()] + df.values.tolist()

    num_rows, num_cols = len(values), len(values[0])  # Ajustado para asegurar todas las filas
    range_name = get_range(start_cell, num_rows, num_cols)

    print(f"📌 Escribiendo en el rango: {range_name}")  

    write_to_sheet(sheets_service, sheet_id, sheet_name, range_name, values)
    
    
    
def delete_sheet(sheets_service, sheet_id, sheet_name):
    """Elimina una hoja dentro de un Google Sheet por su nombre."""
    try:
        # Obtener todas las hojas del Google Sheet
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheets = spreadsheet.get("sheets", [])
        
        # Buscar el sheetId de la hoja a eliminar
        sheet_id_to_delete = None
        for sheet in sheets:
            if sheet["properties"]["title"] == sheet_name:
                sheet_id_to_delete = sheet["properties"]["sheetId"]
                break
        
        if sheet_id_to_delete is None:
            print(f"⚠️ La hoja '{sheet_name}' no existe en el Google Sheet.")
            return
        
        # Crear la solicitud de eliminación
        requests = [{
            "deleteSheet": {
                "sheetId": sheet_id_to_delete
            }
        }]
        
        # Ejecutar la solicitud
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id, 
            body={"requests": requests}
        ).execute()
        
        print(f"✅ Hoja '{sheet_name}' eliminada correctamente.")
    
    except HttpError as error:
        print(f"⚠️ Error al eliminar la hoja '{sheet_name}': {error}")

