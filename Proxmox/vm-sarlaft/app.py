from flask import Flask, request, jsonify
from datetime import datetime
import requests

app = Flask(__name__)

LOGS_URL = "http://192.168.110.24:5003/log"
UMBRAL_SMMLV = 10
SMMLV_2026 = 1423500
UMBRAL_MONTO = UMBRAL_SMMLV * SMMLV_2026

operaciones = []

def registrar_log(operacion, cedula, detalle):
    try:
        requests.post(LOGS_URL, json={
            "servicio": "vm-sarlaft",
            "operacion": operacion,
            "cedula": cedula,
            "detalle": detalle
        }, timeout=2)
    except:
        pass

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "servicio": "modulo-sarlaft"})

@app.route('/analizar', methods=['POST'])
def analizar():
    data = request.get_json()
    cedula = data.get("cedula")
    monto = float(data.get("monto", 0))
    tipo = data.get("tipo", "")
    timestamp = datetime.now().isoformat()

    operacion = {
        "timestamp": timestamp,
        "cedula": cedula,
        "monto": monto,
        "tipo": tipo,
        "sospechosa": False,
        "ros_generado": False
    }

    if monto >= UMBRAL_MONTO:
        operacion["sospechosa"] = True
        operacion["ros_generado"] = True
        registrar_log(
            "ROS_GENERADO",
            cedula,
            f"Operacion inusual detectada: {tipo} por ${monto:,.0f} COP supera umbral de {UMBRAL_SMMLV} SMMLV"
        )

    operaciones.append(operacion)
    registrar_log("analisis_transaccion", cedula, f"Monto: {monto} - Sospechosa: {operacion['sospechosa']}")

    return jsonify({
        "status": "ok",
        "sospechosa": operacion["sospechosa"],
        "ros_generado": operacion["ros_generado"],
        "mensaje": "ROS generado y enviado a Supersolidaria" if operacion["ros_generado"] else "Operacion normal"
    })

@app.route('/operaciones', methods=['GET'])
def ver_operaciones():
    return jsonify(operaciones)

@app.route('/operaciones/sospechosas', methods=['GET'])
def ver_sospechosas():
    sospechosas = [o for o in operaciones if o["sospechosa"]]
    return jsonify(sospechosas)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
