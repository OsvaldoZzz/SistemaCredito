CREATE TABLE IF NOT EXISTS clientes (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL,
  cedula VARCHAR(20) NOT NULL,
  correo VARCHAR(100) NOT NULL,
  password VARCHAR(255) NOT NULL,
  direccion VARCHAR(40) NOT NULL,
  monto DECIMAL(12,2) NOT NULL DEFAULT 0,
  latitud DECIMAL(10,7) NULL,
  longitud DECIMAL(10,7) NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS prestamo (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  monto DECIMAL(12,2) NOT NULL,
  plazo INT NOT NULL,
  estado VARCHAR(20) NOT NULL DEFAULT 'Activo',
  fecha_primer_pago DATE NULL,
  frecuencia_pago VARCHAR(10) NOT NULL DEFAULT 'Mensual',
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pagos_prestamo (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  prestamo_id INT NOT NULL,
  numero_cuota INT NOT NULL,
  monto DECIMAL(12,2) NOT NULL,
  fecha_pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_web_pagos_cuota (prestamo_id, numero_cuota, fecha_pago),
  FOREIGN KEY (prestamo_id) REFERENCES prestamo(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS solicitudes_prestamo (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  monto DECIMAL(12,2) NOT NULL,
  plazo INT NOT NULL,
  frecuencia_pago VARCHAR(10) NOT NULL DEFAULT 'Mensual',
  ingreso_mensual DECIMAL(12,2) NULL,
  estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente',
  fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS citas (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  fecha DATE NOT NULL,
  estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente',
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS web_usuarios (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  usuario VARCHAR(100) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  rol VARCHAR(20) NOT NULL,
  UNIQUE KEY web_usuario_unico (usuario)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS web_asignaciones (
  usuario_id INT NOT NULL,
  cliente_id INT NOT NULL,
  PRIMARY KEY (usuario_id, cliente_id),
  FOREIGN KEY (usuario_id) REFERENCES web_usuarios(id) ON DELETE CASCADE,
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS web_prestamo_tasas (
  prestamo_id INT NOT NULL PRIMARY KEY,
  tasa_interes DECIMAL(6,4) NOT NULL,
  FOREIGN KEY (prestamo_id) REFERENCES prestamo(id) ON DELETE CASCADE
) ENGINE=InnoDB;
