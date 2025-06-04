# ssh_tunnel.py
from sshtunnel import SSHTunnelForwarder
import time
from dotenv import load_dotenv
import os


load_dotenv()


def main():
    tunnel = SSHTunnelForwarder(
        (os.getenv('SSH_HOST'), 22),
        ssh_username=os.getenv('SSH_USER'),
        # ssh_pkey=os.getenv('SSH_PRIVATE_KEY_PATH'),
        ssh_password=os.getenv('SSH_PASSWORD'),
        remote_bind_address=('127.0.0.1', int(os.getenv('DB_PORT_REMOTE'))),
        local_bind_address=('127.0.0.1', int(os.getenv('DB_PORT_LOCAL'))),
        set_keepalive=30
    )

    tunnel.start()
    print(f"Túnel activo en {tunnel.local_bind_host}:{tunnel.local_bind_port}")

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Cerrando túnel...")
        tunnel.stop()


if __name__ == '__main__':
    main()
