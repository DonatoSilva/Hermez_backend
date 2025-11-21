# 📊 Análisis de Modelos - Proyecto Hermez Backend

## 🏗️ Información General del Proyecto

**Framework:** Django 4.x con Django REST Framework  
**Base de Datos:** PostgreSQL (UUID y JSONField)  
**Arquitectura:** API RESTful con WebSockets para tiempo real  
**Autenticación:** JWT con tokens de acceso/refresh

---

## 📋 Modelos por Módulo

### 🔵 MÓDULO USERS

#### **User**

| Campo             | Tipo                 | Descripción                      |
| ----------------- | -------------------- | -------------------------------- |
| `id`              | UUID (PK)            | Identificador único              |
| `username`        | CharField            | Nombre de usuario                |
| `email`           | EmailField           | Correo electrónico               |
| `password`        | CharField            | Contraseña encriptada            |
| `role`            | CharField            | Roles: cliente, conductor, admin |
| `phone`           | CharField            | Teléfono de contacto             |
| `age`             | IntegerField         | Edad del usuario                 |
| `gender`          | CharField            | Género                           |
| `is_online`       | BooleanField         | Estado de conexión               |
| `is_available`    | BooleanField         | Disponibilidad                   |
| `current_vehicle` | ForeignKey → Vehicle | Vehículo actual del domiciliario |
| `created_at`      | DateTimeField        | Fecha de creación                |
| `updated_at`      | DateTimeField        | Última actualización             |

#### **UserRating**

| Campo        | Tipo              | Descripción                   |
| ------------ | ----------------- | ----------------------------- |
| `id`         | UUID (PK)         | Identificador único           |
| `user`       | ForeignKey → User | Usuario calificado            |
| `rating`     | DecimalField      | Puntuación (1-5)              |
| `comment`    | TextField         | Comentario de la calificación |
| `created_at` | DateTimeField     | Fecha de calificación         |

---

### 🟢 MÓDULO ADDRESSES

#### **Address**

| Campo          | Tipo              | Descripción                           |
| -------------- | ----------------- | ------------------------------------- |
| `id`           | UUID (PK)         | Identificador único                   |
| `user`         | ForeignKey → User | Usuario propietario                   |
| `name`         | CharField         | Nombre identificativo de la dirección |
| `address`      | TextField         | Dirección completa                    |
| `city`         | CharField         | Ciudad                                |
| `neighborhood` | CharField         | Barrio/Vecindario                     |
| `isFavorite`   | BooleanField      | Marcada como favorita                 |
| `created_at`   | DateTimeField     | Fecha de creación                     |

---

### 🟡 MÓDULO VEHICLES

#### **VehicleType**

| Campo         | Tipo              | Descripción                 |
| ------------- | ----------------- | --------------------------- |
| `id`          | IntegerField (PK) | Identificador único         |
| `name`        | CharField         | Nombre del tipo de vehículo |
| `description` | TextField         | Descripción detallada       |
| `max_weight`  | DecimalField      | Peso máximo soportado       |
| `created_at`  | DateTimeField     | Fecha de creación           |

#### **Vehicle**

| Campo           | Tipo                     | Descripción              |
| --------------- | ------------------------ | ------------------------ |
| `id`            | UUID (PK)                | Identificador único      |
| `user`          | ForeignKey → User        | Propietario del vehículo |
| `type`          | ForeignKey → VehicleType | Tipo de vehículo         |
| `license_plate` | CharField                | Placa del vehículo       |
| `model`         | CharField                | Modelo del vehículo      |
| `year`          | IntegerField             | Año del vehículo         |
| `color`         | CharField                | Color del vehículo       |
| `is_active`     | BooleanField             | Estado activo/inactivo   |
| `created_at`    | DateTimeField            | Fecha de creación        |

---

### 🔴 MÓDULO DELIVERIES

#### **DeliveryCategory**

| Campo         | Tipo              | Descripción                 |
| ------------- | ----------------- | --------------------------- |
| `id`          | IntegerField (PK) | Identificador único         |
| `name`        | CharField         | Nombre de la categoría      |
| `description` | TextField         | Descripción de la categoría |
| `created_at`  | DateTimeField     | Fecha de creación           |

#### **DeliveryQuote** (Cotización de Entrega)

| Campo              | Tipo                          | Descripción                     |
| ------------------ | ----------------------------- | ------------------------------- |
| `id`               | UUID (PK)                     | Identificador único             |
| `client`           | ForeignKey → User             | Cliente que solicita            |
| `pickup_address`   | TextField                     | Dirección de recogida           |
| `delivery_address` | TextField                     | Dirección de entrega            |
| `category`         | ForeignKey → DeliveryCategory | Categoría de entrega            |
| `description`      | TextField                     | Descripción del paquete         |
| `observations`     | JSONField                     | Lista de observaciones          |
| `estimated_weight` | DecimalField                  | Peso estimado                   |
| `estimated_size`   | CharField                     | Tamaño estimado                 |
| `client_price`     | DecimalField                  | Precio ofrecido por el cliente  |
| `payment_method`   | CharField                     | Método de pago (efectivo/nequi) |
| `status`           | CharField                     | Estado de la cotización         |
| `history_id`       | UUID                          | ID único para el ciclo de vida  |
| `created_at`       | DateTimeField                 | Fecha de creación               |

#### **DeliveryOffer** (Oferta del Conductor)

| Campo            | Tipo                       | Descripción                      |
| ---------------- | -------------------------- | -------------------------------- |
| `id`             | UUID (PK)                  | Identificador único              |
| `quote`          | ForeignKey → DeliveryQuote | Cotización relacionada           |
| `driver`         | ForeignKey → User          | Conductor que oferta             |
| `offered_price`  | DecimalField               | Precio ofrecido por el conductor |
| `estimated_time` | DurationField              | Tiempo estimado de entrega       |
| `vehicle`        | ForeignKey → Vehicle       | Vehículo del conductor           |
| `status`         | CharField                  | Estado de la oferta              |
| `created_at`     | DateTimeField              | Fecha de creación                |

#### **Delivery** (Entrega Final)

| Campo           | Tipo                          | Descripción                  |
| --------------- | ----------------------------- | ---------------------------- |
| `id`            | UUID (PK)                     | Identificador único          |
| `quote`         | OneToOneField → DeliveryQuote | Cotización aprobada          |
| `driver`        | ForeignKey → User             | Conductor asignado           |
| `final_price`   | DecimalField                  | Precio final acordado        |
| `vehicle`       | ForeignKey → Vehicle          | Vehículo usado en la entrega |
| `pickup_time`   | DateTimeField                 | Hora de recogida             |
| `delivery_time` | DateTimeField                 | Hora de entrega              |
| `status`        | CharField                     | Estado de la entrega         |
| `created_at`    | DateTimeField                 | Fecha de creación            |

#### **DeliveryHistory** (Historial de Estados)

| Campo       | Tipo                  | Descripción         |
| ----------- | --------------------- | ------------------- |
| `id`        | UUID (PK)             | Identificador único |
| `delivery`  | ForeignKey → Delivery | Entrega relacionada |
| `status`    | CharField             | Estado registrado   |
| `timestamp` | DateTimeField         | Momento del cambio  |
| `notes`     | TextField             | Notas adicionales   |

---

## 🔗 Relaciones Entre Modelos

### Diagrama de Relaciones

```
User (1) ──────< (N) Address
  │
  │
User (1) ──────< (N) Vehicle
  │
  │
Vehicle (1) ──────< (N) DeliveryOffer
  │
  │
User (1) ──────1─── (0-1) current_vehicle
  │
  │
Vehicle (1) ──────< (N) Delivery
  │
  │
User (1) ──────< (N) DeliveryQuote (client)
  │
  │
User (1) ──────< (N) DeliveryOffer (driver)
  │
  │
User (1) ──────< (N) Delivery (driver)
  │
  │
User (1) ──────< (N) UserRating

DeliveryCategory (1) ──────< (N) DeliveryQuote

DeliveryQuote (1) ──────< (N) DeliveryOffer

DeliveryQuote (1) ────1─── (1) Delivery

Delivery (1) ──────< (N) DeliveryHistory
```

### Leyenda de Relaciones

- `(1)` → Uno
- `(N)` → Muchos
- `──1──` → Relación Uno a Uno
- `─────<` → Relación Uno a Muchos (FK)

---

## 🎨 Sugerencias para el Diagrama ER

### Colores por Módulo

- **🔵 Azul**: Módulo Users
- **🟢 Verde**: Módulo Addresses
- **🟡 Amarillo**: Módulo Vehicles
- **🔴 Rojo**: Módulo Deliveries

### Convenciones de Campos

- **PK**: Primary Key (subrayado o negrita)
- **FK**: Foreign Key (itálico)
- **JSONField**: Campos especiales con etiqueta
- **UUID**: Campos de identificación única

### Tipos de Relaciones Visuales

- **Línea continua**: Relación 1:N
- **Línea con rombo**: Relación 1:1
- **Flechas**: Dirección de la Foreign Key

---

## 📈 Flujo de Datos Principal

1. **Cliente** crea **DeliveryQuote** → Selecciona **DeliveryCategory**
2. **Conductores** crean **DeliveryOffer** para la cotización
3. **Cliente** acepta una oferta → Se crea **Delivery**
4. **Sistema** registra cambios en **DeliveryHistory**
5. **Entrega** se completa → Se actualiza estado final

---

## ⏱ Expiración Automática

- Cada **cotización** incluye el campo `expires_at` y se elimina automáticamente cuando expira ejecutando el comando `python manage.py expire_quotes_offers` (idealmente programado desde cron o un scheduler).
- Las **ofertas** expiran en 4 minutos por defecto; sus `expires_at` también pueden extenderse mediante el endpoint `POST /deliveries/api/offers/{id}/extend-expiration/` enviando `{ "minutes": 2 }`.
- Las cotizaciones se pueden extender desde `POST /deliveries/api/quotes/{id}/extend-expiration/`.
- Ajusta las constantes `DELIVERIES_QUOTE_TTL_MINUTES` y `DELIVERIES_OFFER_TTL_MINUTES` en `backend/settings.py` para personalizar los tiempos.

---

_Generado para diagrama entidad-relación del proyecto Hermez Backend_
