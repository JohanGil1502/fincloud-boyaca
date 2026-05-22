-- Base de datos CoopBoyacá Ahorro y Crédito
-- Esquema y datos de prueba PostgreSQL

CREATE DATABASE coopboyaca;
\c coopboyaca

CREATE TABLE asociados (
    id SERIAL PRIMARY KEY,
    cedula VARCHAR(15) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    saldo DECIMAL(12,2) DEFAULT 0,
    fecha_ingreso DATE DEFAULT CURRENT_DATE
);

INSERT INTO asociados (cedula, nombre, saldo) VALUES
('1234567890', 'Carlos Pérez Ruiz', 2500000),
('0987654321', 'María González López', 1800000),
('1122334455', 'Jorge Rodríguez Silva', 3200000),
('5566778899', 'Ana Cifuentes Mora', 950000),
('9988776655', 'Luis Herrera Castro', 4100000);

CREATE USER fincloud WITH PASSWORD 'fincloud2024';
GRANT ALL PRIVILEGES ON DATABASE coopboyaca TO fincloud;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fincloud;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fincloud;
