import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build


# Definir los scopes necesarios
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.readonly',
          'https://www.googleapis.com/auth/drive.file']


# Definir la ruta al archivo de credenciales
google_credentials_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials', 'google_services', 'google_service_account.json')



def authenticate_with_service_account():
    """Autenticación con Google API usando cuenta de servicio para Sheets y Drive."""
    
    # Cargar las credenciales de la cuenta de servicio
    creds = service_account.Credentials.from_service_account_file(
        google_credentials_path, scopes=SCOPES)
    
    # Crear servicios de Google Sheets y Google Drive
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    return sheets_service, drive_service

