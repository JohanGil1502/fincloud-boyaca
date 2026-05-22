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
| **Fog** | Regional — Azure Colombia | Portal web, Consulta de saldo, Backup cifrado, Entra ID |
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

- Proxmox VE 8.x instalado y accesible en la red local
- 4 VMs Ubuntu Server 22.04 clonadas desde plantilla base
- Cuenta de Azure for Students con grupo de recursos `fincloud-boyaca-rg`
- Python 3.10+ en cada VM
- PostgreSQL 14+ en vm-database

---

## Instrucciones de despliegue

### 1. Clonar el repositorio en cada VM

Conectarse por SSH a cada VM y clonar el repositorio:

```bash
ssh fincloud@192.168.110.21   # vm-sico
git clone https://github.com/JohanGil1502/fincloud-boyaca.git
cd fincloud-boyaca
```

Repetir para cada VM con su IP correspondiente:

| VM | IP |
|---|---|
| vm-sico | 192.168.110.21 |
| vm-sarlaft | 192.168.110.22 |
| vm-database | 192.168.110.23 |
| vm-logs | 192.168.110.24 |

---

### 2. Desplegar vm-database (primero)

```bash
ssh fincloud@192.168.110.23
sudo -u postgres psql < fincloud-boyaca/proxmox/vm-database/init.sql
```

---

### 3. Desplegar vm-sico

```bash
ssh fincloud@192.168.110.21
cd fincloud-boyaca/proxmox/vm-sico
pip3 install -r requirements.txt --break-system-packages
python3 app.py &
```

El servicio quedará disponible en `http://192.168.110.21:5000`

---

### 4. Desplegar vm-sarlaft

```bash
ssh fincloud@192.168.110.22
cd fincloud-boyaca/proxmox/vm-sarlaft
pip3 install -r requirements.txt --break-system-packages
python3 app.py &
```

El servicio quedará disponible en `http://192.168.110.22:5001`

---

### 5. Desplegar vm-logs

```bash
ssh fincloud@192.168.110.24
cd fincloud-boyaca/proxmox/vm-logs
pip3 install -r requirements.txt --break-system-packages
python3 app.py &
```

El servicio quedará disponible en `http://192.168.110.24:5002`

---

### 6. Configurar el backup hacia Azure Blob

En vm-database editar el script con la cadena de conexión de Azure:

```bash
nano fincloud-boyaca/azure/backup.sh
```

Reemplazar `TU_CONNECTION_STRING` con la cadena de conexión del Storage Account `fincloudbackup`. Luego ejecutar:

```bash
chmod +x fincloud-boyaca/azure/backup.sh
./fincloud-boyaca/azure/backup.sh
```

Para automatizar el backup cada hora:

```bash
crontab -e
# Agregar esta línea:
0 * * * * /home/fincloud/fincloud-boyaca/azure/backup.sh
```

---

## Verificación del despliegue

Una vez todas las VMs estén corriendo, verificar que los servicios responden:

```bash
# Desde cualquier equipo en la red
curl http://192.168.110.21:5000/health    # SICO
curl http://192.168.110.22:5001/health    # SARLAFT
curl http://192.168.110.24:5002/health    # Logs
```

Todos deben responder `{"status": "ok"}`.

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
| `fincloud-boyaca` | App Service | Portal web de CoopBoyacá |

---

*Cloud Summit UPTC 2026 · FinCloud Boyacá · Electiva I — IaaS y Virtualización · UPTC*