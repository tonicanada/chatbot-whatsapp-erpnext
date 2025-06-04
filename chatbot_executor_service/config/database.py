# config/database.py
import os
import json
import sqlalchemy
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder

load_dotenv()

# tunnel = None
db_list = json.loads(os.getenv("DB_LIST"))

# def start_ssh_tunnel():
#     global tunnel
#     if tunnel and tunnel.is_active:
#         return tunnel  # ya iniciado

#     tunnel = SSHTunnelForwarder(
#         (os.getenv('SSH_HOST'), 22),
#         ssh_username=os.getenv('SSH_USER'),
#         ssh_pkey=os.getenv('SSH_PRIVATE_KEY_PATH'),
#         remote_bind_address=('127.0.0.1', int(os.getenv('DB_PORT_REMOTE'))),
#         local_bind_address=('127.0.0.1', int(os.getenv('DB_PORT_LOCAL'))),
#         set_keepalive=30 
#     )
#     tunnel.start()
#     print(f"🔐 Túnel SSH iniciado en 127.0.0.1:{tunnel.local_bind_port}")
#     return tunnel

# def stop_ssh_tunnel():
#     global tunnel
#     if tunnel:
#         tunnel.stop()
#         print("🔌 Túnel SSH cerrado")

def get_db_connection(company_name):
    db_name = db_list.get(company_name)
    if not db_name:
        raise ValueError(f"No se encontró la base de datos para la empresa {company_name}")

    db_url = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@127.0.0.1:{int(os.getenv('DB_PORT_LOCAL')) }/{db_name}"
    engine = sqlalchemy.create_engine(db_url)
    connection = engine.connect()
    return connection