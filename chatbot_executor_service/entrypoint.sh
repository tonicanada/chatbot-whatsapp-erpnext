#!/bin/bash
set -e

# Función para limpiar el túnel al recibir señal de salida
function cleanup {
  echo "Deteniendo túnel SSH..."
  kill $TUNNEL_PID
  wait $TUNNEL_PID 2>/dev/null
  exit 0
}

# Capturar señales para limpieza
trap cleanup SIGINT SIGTERM

echo "Iniciando túnel SSH..."
python infra/ssh_tunnel.py &

TUNNEL_PID=$!

# Esperar un poco para que el túnel se establezca
sleep 3

echo "Arrancando Gunicorn..."
exec gunicorn -k eventlet --log-level debug --timeout 0 --worker-connections 1000 -b 0.0.0.0:5000 app:app
