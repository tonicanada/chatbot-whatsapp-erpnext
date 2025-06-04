import io
import os
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload


def download_and_save_file_from_drive(drive_service, file_id, save_dir=".", custom_filename=None):
    try:
        file_metadata = drive_service.files().get(
            fileId=file_id, 
            fields="name",
            supportsAllDrives=True
        ).execute()

        # Si se proporciona un nombre personalizado, lo usa; de lo contrario, usa el original
        file_name = custom_filename if custom_filename else file_metadata["name"]
        save_path = os.path.join(save_dir, file_name)

        # Descargar el archivo
        request = drive_service.files().get_media(fileId=file_id, supportsAllDrives=True)
        with open(save_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Descargando... {int(status.progress() * 100)}%")

        print(f"Archivo guardado en: {save_path}")
        return save_path

    except HttpError as error:
        print(f"Ocurrió un error: {error}")
        return None
    
    
    
def upload_file_to_drive(drive_service, file_path, folder_id):
    try:
        file_name = os.path.basename(file_path)
        
        file_metadata = {
            "name": file_name,
            "parents": [folder_id]
        }

        media = MediaFileUpload(file_path, resumable=True)

        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True
        ).execute()

        print(f"Archivo subido con éxito. File ID: {uploaded_file.get('id')}")
        return uploaded_file.get("id")

    except HttpError as error:
        print(f"Ocurrió un error: {error}")
        return None