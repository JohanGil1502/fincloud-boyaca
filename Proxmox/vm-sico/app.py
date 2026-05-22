from flask import Flask, request, jsonify
import psycopg2
from datetime import datetime
import requests

app = Flask(__name__)

DB_CONFIG = {
    "host": "192.168.110.23",
    "database": "coopboyaca",
    "user": "fincloud",
    "password": "fincloud2024"
}

LOGS_URL = "http://192.168.110.24:5003/log"

def registrar_log(operacion, cedula, detalle):
    try:
        requests.post(LOGS_URL, json={
            "servicio": "vm-sico",
            "operacion": operacion,
            "cedula": cedula,
            "detalle": detalle
        }, timeout=2)
    except:
        pass

def get_db():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "servicio": "core-sico"})

@app.route('/saldo/<cedula>', methods=['GET'])
def consultar_saldo(cedula):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT nombre, saldo FROM asociados WHERE cedula = %s", (cedula,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return jsonify({"error": "Asociado no encontrado"}), 404
        registrar_log("consulta_saldo", cedula, f"Saldo consultado: {row[1]}")
        return jsonify({"cedula": cedula, "nombre": row[0], "saldo": float(row[1])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transaccion', methods=['POST'])
def transaccion():
    data = request.get_json()
    cedula = data.get("cedula")
    tipo = data.get("tipo")
    monto = float(data.get("monto", 0))
    try:
        conn = get_db()
        cur = conn.cursor()
        if tipo == "consignacion":
            cur.execute("UPDATE asociados SET saldo = saldo + %s WHERE cedula = %s", (monto, cedula))
        elif tipo == "retiro":
            cur.execute("UPDATE asociados SET saldo = saldo - %s WHERE cedula = %s RETURNING saldo", (monto, cedula))
            row = cur.fetchone()
            if row and row[0] < 0:
                conn.rollback()
                return jsonify({"error": "Saldo insuficiente"}), 400
        conn.commit()
        cur.close()
        conn.close()
        registrar_log(tipo, cedula, f"Monto: {monto}")
        return jsonify({"status": "ok", "operacion": tipo, "monto": monto})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
