#!/bin/bash

# FinCloud Boyacá — Script de backup automático hacia Azure Blob Storage
# Ejecutar desde Proxmox — cron: 0 * * * * /root/backup_azure.sh

FECHA=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/tmp/coopboyaca_$FECHA.sql"
CONTAINER="backups"
CONNECTION_STRING="TU_CONNECTION_STRING_AQUI"

echo "[$(date)] Iniciando backup de CoopBoyacá..."

# Generar backup de PostgreSQL desde vm-database
echo "[$(date)] Generando volcado SQL desde vm-database (192.168.110.23)..."
ssh grupo3@192.168.110.23 "PGPASSWORD=fincloud2024 pg_dump -h localhost -U fincloud coopboyaca" > $BACKUP_FILE

if [ $? -ne 0 ]; then
    echo "[$(date)] ERROR: No se pudo generar el backup de PostgreSQL"
    exit 1
fi

echo "[$(date)] Backup generado: $BACKUP_FILE ($(du -sh $BACKUP_FILE | cut -f1))"

# Subir a Azure Blob Storage
echo "[$(date)] Subiendo a Azure Blob Storage (contenedor: $CONTAINER)..."
az storage blob upload \
  --connection-string "$CONNECTION_STRING" \
  --container-name $CONTAINER \
  --name "backup_$FECHA.sql" \
  --file $BACKUP_FILE \
  --overwrite

if [ $? -ne 0 ]; then
    echo "[$(date)] ERROR: No se pudo subir el backup a Azure"
    rm $BACKUP_FILE
    exit 1
fi

# Eliminar backup local temporal
rm $BACKUP_FILE
echo "[$(date)] Backup completado exitosamente: backup_$FECHA.sql"
echo "[$(date)] RPO garantizado: menos de 1 hora"
