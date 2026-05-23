# FinCloud Boyacá — Infraestructura Cloud Híbrida para CoopBoyacá

**Cloud Summit UPTC 2026 · Transformación Digital Sectorial: de Boyacá a la Nube**  
Ingeniería de Sistemas y Computación · Universidad Pedagógica y Tecnológica de Colombia

---

## Descripción del proyecto

Este repositorio contiene el prototipo funcional de la propuesta de infraestructura cloud híbrida diseñada por **FinCloud Boyacá** para **CoopBoyacá Ahorro y Crédito**, una cooperativa financiera con sede en Tunja, Boyacá.

La solución combina una nube privada sobre **Proxmox VE** on-premise con servicios de **Microsoft Azure**, distribuida en tres capas de procesamiento:

| Capa | Alcance | Componentes |
|---|---|---|
| **Edge** | Local — Sede Tunja | Core SICO, Módulo SARLAFT, BD de asociados, Logs de auditoría |
| **Fog** | Regional — Azure | Portal web, Consulta de saldo, Backup cifrado, Entra ID |
| **Cloud** | Nacional | Supersolidaria, Reportes ROS, Gestión de identidad global |

---

## Equipo

| Integrante | Rol | Responsabilidades |
|---|---|---|
| David Cubillos | Arquitecto Cloud | Diseño de la arquitectura, modelo de despliegue, modelos de servicio |
| Walter Alfonso | Ingeniero Cloud | Implementación Proxmox, repositorio, portal web, video demo |
| Brayan Cifuentes | Consultor de Negocio | Investigación regulatoria, costos CapEx/OpEx, informe técnico |
| Johan Gil | Gerente del Proyecto | Coordinación, plan de trabajo, logística del Cloud Summit |

---

## Estructura del repositorio

```
fincloud-boyaca/
│
├── index.html              # Portal web de FinCloud Boyacá (GitHub Pages)
├── README.md               # Este archivo
│
├── proxmox/
│   ├── vm-sico/            # Servicio simulado del core bancario SICO
│   │   ├── app.py          # Aplicación Flask — transacciones y saldos
│   │   └── requirements.txt
│   │
│   ├── vm-sarlaft/         # Módulo SARLAFT simulado
│   │   ├── app.py          # Detección de operaciones inusuales y ROS
│   │   └── requirements.txt
│   │
│   ├── vm-database/        # Base de datos de asociados
│   │   └── init.sql        # Esquema y datos de prueba PostgreSQL
│   │
│   └── vm-logs/            # Servicio de logs de auditoría
│       ├── app.py          # Registro inmutable de transacciones
│       └── requirements.txt
│
└── azure/
    └── backup.sh           # Script de backup automático hacia Azure Blob
```

---

## Requisitos previos

- Proxmox VE 8.x instalado y operativo
- 4 VMs con Ubuntu Server 22.04 LTS
- Python 3.10+ en cada VM
- PostgreSQL 14+ en vm-database
- Cuenta de Azure con grupo de recursos `fincloud-boyaca-rg`
- Azure CLI instalado en el nodo Proxmox
- Git instalado en cada VM

---

## Paso 1 — Instalar Proxmox VE

1. Descargar la ISO desde https://www.proxmox.com/en/downloads
2. Crear USB booteable con Rufus o Balena Etcher
3. Arrancar el equipo desde la USB (F12 en la mayoría de equipos para el menú de boot)
4. Seguir el instalador gráfico:
   - Seleccionar el disco de instalación
   - Zona horaria: **America/Bogota**
   - Contraseña del usuario `root`
   - IP estática (ejemplo: `192.168.110.2/24`, gateway `192.168.110.1`)
5. Al terminar, retirar la USB y reiniciar
6. Acceder a la interfaz web desde cualquier equipo en la red:

```
https://192.168.110.2:8006
```

Iniciar sesión con usuario `root` y la contraseña configurada.

> **Nota:** Si el disco tiene particiones previas y la instalación falla, limpiar el disco desde la consola del instalador con `Ctrl+Alt+F2` y ejecutar `wipefs -a /dev/sda && sgdisk --zap-all /dev/sda`, luego reiniciar con `Ctrl+Alt+F1`.

---

## Paso 2 — Crear la VM base en Proxmox

En la interfaz web de Proxmox:

1. Subir la ISO de Ubuntu Server 22.04: **local → ISO Images → Upload**
2. Clic en **Create VM** y configurar:
   - **Name:** `ubuntu-base`
   - **ISO:** Ubuntu Server 22.04
   - **Disk:** 2 GB
   - **CPU:** 2 core
   - **Memory:** 4096 MB
   - **Network:** bridge `vmbr0`
3. Iniciar la VM y seguir el instalador de Ubuntu:
   - Configurar IP estática (ejemplo: `192.168.110.10/24`, gateway `192.168.110.1`, DNS `8.8.8.8`)
   - Crear usuario: `grupo3`
   - Activar **OpenSSH server** durante la instalación
4. Conectarse por SSH y actualizar:

```bash
ssh grupo3@192.168.110.10
sudo apt update && sudo apt upgrade -y
```

5. Instalar los paquetes base:

```bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-client git curl
```

6. Crear el entorno virtual Python:

```bash
python3 -m venv ~/venv
source ~/venv/bin/activate
pip install flask psycopg2-binary requests
```

7. Apagar la VM:

```bash
sudo shutdown -h now
```

8. En Proxmox, clic derecho sobre la VM → **Convert to Template**

---

## Paso 3 — Clonar las 4 VMs desde la plantilla

Clic derecho sobre la plantilla → **Clone** para cada VM. Seleccionar **Full Clone**:

| VM | ID | IP | Servicio |
|---|---|---|---|
| vm-sico | 101 | 192.168.110.21 | Core bancario SICO |
| vm-sarlaft | 102 | 192.168.110.22 | Módulo SARLAFT |
| vm-database | 103 | 192.168.110.23 | Base de datos PostgreSQL |
| vm-logs | 104 | 192.168.110.24 | Logs de auditoría |

---

## Paso 4 — Configurar la IP de cada VM clonada

Iniciar cada VM, entrar a su consola y editar el archivo de red:

```bash
sudo nano /etc/netplan/01-config.yaml
```

Ejemplo para `vm-sico`:

```yaml
network:
  version: 2
  ethernets:
    ens18:
      dhcp4: no
      addresses:
        - 192.168.110.21/24
      routes:
        - to: default
          via: 192.168.110.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
```

Aplicar y verificar:

```bash
sudo netplan apply
ping 192.168.110.2   # debe responder
```

Repetir para cada VM cambiando solo la IP.

---

## Paso 5 — Desplegar vm-database (hacerlo primero)

```bash
ssh grupo3@192.168.110.23
```

Activar PostgreSQL:

```bash
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

Crear la base de datos:

```bash
sudo -u postgres psql < ~/fincloud-boyaca/proxmox/vm-database/init.sql
```

Configurar acceso desde la red interna:

```bash
# Editar postgresql.conf
sudo nano /etc/postgresql/*/main/postgresql.conf
# Cambiar la línea: listen_addresses = '*'

# Editar pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf
# Agregar al final:
# host    coopboyaca    fincloud    192.168.110.0/24    md5

sudo systemctl restart postgresql
```

Verificar:

```bash
ss -tlnp | grep 5432
# Debe mostrar 0.0.0.0:5432
```

---

## Paso 6 — Desplegar vm-sico

```bash
ssh grupo3@192.168.110.21
source ~/venv/bin/activate
pip install requests   # si no está instalado
mkdir -p /opt/sico
cp ~/fincloud-boyaca/proxmox/vm-sico/app.py /opt/sico/sico_service.py
```

Crear el servicio systemd:

```bash
sudo nano /etc/systemd/system/sico.service
```

```ini
[Unit]
Description=Servicio Core Bancario SICO — CoopBoyacá
After=network.target

[Service]
User=grupo3
WorkingDirectory=/opt/sico
ExecStart=/home/grupo3/venv/bin/python3 /opt/sico/sico_service.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable sico
sudo systemctl start sico
```

Verificar:

```bash
curl http://192.168.110.21:5000/health
# {"status": "ok", "servicio": "core-sico"}
```

---

## Paso 7 — Desplegar vm-sarlaft

```bash
ssh grupo3@192.168.110.22
source ~/venv/bin/activate
mkdir -p /opt/sarlaft
cp ~/fincloud-boyaca/proxmox/vm-sarlaft/app.py /opt/sarlaft/sarlaft_service.py
```

Crear el servicio systemd:

```bash
sudo nano /etc/systemd/system/sarlaft.service
```

```ini
[Unit]
Description=Módulo SARLAFT — CoopBoyacá
After=network.target

[Service]
User=grupo3
WorkingDirectory=/opt/sarlaft
ExecStart=/home/grupo3/venv/bin/python3 /opt/sarlaft/sarlaft_service.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable sarlaft
sudo systemctl start sarlaft
```

Verificar:

```bash
curl http://192.168.110.22:5001/health
# {"status": "ok", "servicio": "modulo-sarlaft"}
```

---

## Paso 8 — Desplegar vm-logs

```bash
ssh grupo3@192.168.110.24
source ~/venv/bin/activate
mkdir -p /opt/auditoria
cp ~/fincloud-boyaca/proxmox/vm-logs/app.py /opt/auditoria/logs_service.py
```

Crear el servicio systemd:

```bash
sudo nano /etc/systemd/system/auditoria.service
```

```ini
[Unit]
Description=Servicio de Logs de Auditoría CoopBoyacá
After=network.target

[Service]
User=grupo3
WorkingDirectory=/opt/auditoria
ExecStart=/home/grupo3/venv/bin/python3 /opt/auditoria/logs_service.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable auditoria
sudo systemctl start auditoria
```

Verificar:

```bash
curl http://192.168.110.24:5003/health
# {"status": "ok", "servicio": "auditoria-logs"}
```

---

## Paso 9 — Verificación del despliegue completo

Desde el nodo Proxmox, ejecutar en orden:

```bash
# 1. Health check de todos los servicios
curl http://192.168.110.21:5000/health
curl http://192.168.110.22:5001/health
curl http://192.168.110.24:5003/health

# 2. Consultar saldo (prueba SICO + BD)
curl http://192.168.110.21:5000/saldo/1234567890
# Esperado: {"cedula":"1234567890","nombre":"Carlos Pérez Ruiz","saldo":2500000.0}

# 3. Registrar una transacción
curl -X POST http://192.168.110.21:5000/transaccion \
  -H "Content-Type: application/json" \
  -d '{"cedula":"1234567890","tipo":"retiro","monto":500000}'
# Esperado: {"status":"ok","operacion":"retiro","monto":500000.0}

# 4. Probar detección SARLAFT (supera 10 SMMLV = $14.235.000 COP)
curl -X POST http://192.168.110.22:5001/analizar \
  -H "Content-Type: application/json" \
  -d '{"cedula":"1234567890","monto":15000000,"tipo":"consignacion"}'
# Esperado: {"ros_generado":true,"sospechosa":true}

# 5. Ver logs de auditoría registrados
curl http://192.168.110.24:5003/logs
```

---

## Paso 10 — Configurar el backup hacia Azure Blob Storage

Instalar el Azure CLI en el nodo Proxmox:

```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | bash
```

Autenticarse:

```bash
az login --use-device-code
```

Editar el script con la cadena de conexión real del Storage Account:

```bash
nano /root/backup_azure.sh
# Reemplazar TU_CONNECTION_STRING_AQUI con la cadena de conexión de Azure
chmod +x /root/backup_azure.sh
```

Ejecutar manualmente para verificar:

```bash
/root/backup_azure.sh
# Debe mostrar: Backup completado exitosamente: backup_YYYYMMDD_HHMMSS.sql
```

Automatizar con cron cada hora:

```bash
crontab -e
# Agregar al final:
0 * * * * /root/backup_azure.sh
```

Verificar en el portal de Azure: **fincloudbackup → Contenedores → backups**

---

## Marco regulatorio

| Norma | Aplicación en la arquitectura |
|---|---|
| Circular 007 Supersolidaria | Logs de auditoría inmutables en vm-logs (Proxmox, Colombia) |
| SARLAFT | Módulo de detección en vm-sarlaft, reportes ROS automáticos en < 24 h |
| Ley 1581 de 2012 | Todos los datos personales en Proxmox, nunca salen del territorio nacional |

---

## Portal web

El portal de FinCloud Boyacá está publicado en:

**[https://JohanGil1502.github.io/fincloud-boyaca](https://JohanGil1502.github.io/fincloud-boyaca)**

---

## Recursos en Azure

| Recurso | Tipo | Propósito |
|---|---|---|
| `fincloud-boyaca-rg` | Grupo de recursos | Contenedor de todos los recursos Azure del proyecto |
| `fincloudbackup` | Storage Account | Backup cifrado de la BD de asociados desde Proxmox |
| `fincloud-boyaca` | App Service | Portal web de CoopBoyacá (aprovisionado) |

---

*Cloud Summit UPTC 2026 · FinCloud Boyacá · Electiva I — IaaS y Virtualización · UPTC*