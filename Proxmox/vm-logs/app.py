from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
LOG_FILE = "/opt/auditoria/audit.log"

def escribir_log(entrada):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entrada) + "\n")

@app.route('/log', methods=['POST'])
def registrar():
    data = request.get_json()
    entrada = {
        "timestamp": datetime.now().isoformat(),
        "servicio": data.get("servicio", "desconocido"),
        "operacion": data.get("operacion", ""),
        "cedula": data.get("cedula", ""),
        "detalle": data.get("detalle", "")
    }
    escribir_log(entrada)
    return jsonify({"status": "ok", "mensaje": "Log registrado"}), 201

@app.route('/logs', methods=['GET'])
def ver_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])
    with open(LOG_FILE, "r") as f:
        lineas = f.readlines()
    logs = [json.loads(l) for l in lineas if l.strip()]
    return jsonify(logs)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "servicio": "auditoria-logs"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
