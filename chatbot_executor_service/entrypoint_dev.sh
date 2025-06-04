#!/bin/bash
# entrypoint_dev.sh

# Ejecutar túnel SSH en background
python infra/ssh_tunnel.py &

# Guardar PID del túnel
SSH_TUNNEL_PID=$!

# Ejecutar Flask en modo desarrollo con autoreload
# python app.py
echo "Arrancando Gunicorn..."
exec gunicorn -k eventlet --reload --workers 1 -b 0.0.0.0:5000 app:app

# Cuando app.py termine, matar túnel SSH
kill $SSH_TUNNEL_PID
