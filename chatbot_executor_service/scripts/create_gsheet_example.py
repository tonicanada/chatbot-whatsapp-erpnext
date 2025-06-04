import sys
import os
from datetime import datetime

# Asegurar que se pueda importar desde utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.google_services_auth import authenticate_with_service_account
from utils.google_sheet_utils import create_google_sheet, write_to_sheet


FOLDER_ID = "15XET6Tu61pyZPjSs_wwGIvayKDaW-4G_"


def create_gsheet_example():
    """Crea un Google Sheet en la unidad compartida y agrega una tabla de ejemplo."""
    
    # Autenticarse con Google API
    sheets_service, drive_service = authenticate_with_service_account()
    
    # Crear el Google Sheet en la unidad compartida con 
    # Generate a title with this pattern "YYYYMMDD_HHMMSS_gsheet_example_from_python"
    title = datetime.now().strftime("%Y%m%d_%H%M%S_gsheet_example_from_python")
    
    
    sheet_id = create_google_sheet(sheets_service, drive_service, title=title, folder_id=FOLDER_ID)
    print(f"Google Sheet creado: https://docs.google.com/spreadsheets/d/{sheet_id}")
    
        # Datos de ejemplo para escribir en el sheet
    data = [
        ["Nombre", "Edad", "Ciudad"],
        ["Alice", 30, "Madrid"],
        ["Bob", 25, "Barcelona"],
        ["Carlos", 35, "Sevilla"]
    ]

    # Escribir datos en el Google Sheet
    write_to_sheet(sheets_service, sheet_id, "A1", data)
    print("Datos de ejemplo escritos en el Google Sheet.")