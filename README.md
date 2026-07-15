# Back Office · Mini App Toka

Back office para la mini app, con **APIs REST** para que la mini app consuma
información (catálogo, ads, direcciones) y para recibir desde la mini app / el
backend de Toka los **pedidos** y **pagos confirmados**.

## Stack

- **Backend:** Django 5 + Django REST Framework + PostgreSQL (JWT auth)
- **Frontend:** React + TypeScript (Vite)
- **DB:** PostgreSQL (credenciales en `backend/.env`)

## Estructura

```
.
├── backend/            # API Django REST Framework
│   ├── config/         # settings, urls, wsgi/asgi
│   ├── apps/
│   │   ├── users/              # Administrador de usuarios y roles
│   │   ├── catalog/            # Gestión de catálogo
│   │   ├── inventory/          # Gestión de inventarios
│   │   ├── orders/             # Pedidos + clientes + direcciones guardadas
│   │   ├── payments/           # Transacciones de pago + webhook Toka
│   │   ├── ads/                # Carrusel de ads (hasta 4 fotos)
│   │   ├── reverse_logistics/  # Logística inversa (campos por confirmar)
│   │   ├── reports/            # Reportes posventa (por confirmar)
│   │   └── toka/               # Integración con la super app de Toka
│   ├── .env            # <-- COMPLETA AQUÍ tus credenciales
│   └── requirements.txt
└── frontend/           # Back office en React + TypeScript
    └── src/
        ├── api/        # cliente axios + tipos
        ├── auth/       # contexto de autenticación (JWT)
        ├── components/ # layout, sidebar, rutas protegidas
        └── pages/      # una página por módulo
```

## Roles

`ADMINISTRADOR`, `PROCUREMENT`, `LOGISTIC`, `SALES`. El administrador ve todo; los
demás ven los módulos asignados (configurable en `frontend/src/components/nav.ts`
y en `allowed_roles` de cada ViewSet del backend).

---

## 1) Backend — puesta en marcha

> Las dependencias ya están instaladas en `backend/.venv`.

### a. Completar credenciales

Edita **`backend/.env`** y coloca:

```
DB_NAME=backoffice_toka
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD
DB_HOST=127.0.0.1
DB_PORT=5432

TOKA_API_BASE_URL=https://api.toka.example.com
TOKA_API_KEY=TU_API_KEY
TOKA_WEBHOOK_SECRET=UN_SECRETO_FUERTE
```

Crea la base de datos en PostgreSQL (una sola vez):

```sql
CREATE DATABASE backoffice_toka;
```

### b. Migraciones (⚠️ ejecutar SOLO cuando lo indiques)

> Dejé todo configurado pero **no corrí migraciones**, tal como pediste.
> Cuando estés listo:

```bash
cd backend
.venv\Scripts\activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # primer usuario (rol se ajusta en el admin)
```

### c. Levantar el servidor

```bash
python manage.py runserver
```

- API:            http://127.0.0.1:8000/api/
- Documentación:  http://127.0.0.1:8000/api/docs/  (Swagger, requiere sesión iniciada en /admin/)
- Admin Django:   http://127.0.0.1:8000/admin/

📖 **Guía de uso de las APIs para desarrolladores:** [docs/API_GUIDE.md](docs/API_GUIDE.md)

---

## 2) Frontend — puesta en marcha

```bash
cd frontend
npm install        # si aún no lo hiciste
npm run dev        # http://localhost:5173
```

La URL de la API se configura en `frontend/.env` (`VITE_API_URL`).

---

## APIs principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/token/` | Login (devuelve access, refresh y datos del usuario) |
| POST | `/api/auth/token/refresh/` | Renovar token |
| CRUD | `/api/users/` | Usuarios y roles (solo Administrador) |
| CRUD | `/api/categories/`, `/api/products/` | Catálogo |
| GET/PATCH | `/api/inventory/` | Inventario (editar unidades) |
| CRUD | `/api/customers/`, `/api/customer-addresses/` | Clientes y direcciones guardadas |
| CRUD | `/api/orders/` | Pedidos |
| GET | `/api/payments/` | Transacciones de pago |
| CRUD | `/api/carousels/`, `/api/carousel-images/` | Ads / carrusel |
| GET | `/api/reports/summary/` | KPIs del dashboard |

### Integración con Toka

- **Traer datos del cliente** desde la super app:
  `POST /api/toka/customers/<toka_customer_id>/sync/`
  Crea/actualiza el cliente y guarda su dirección de entrega.

- **Webhook de confirmación de pago** (lo llama el backend de Toka):
  `POST /api/webhooks/toka/payment/`
  Header requerido: `X-Toka-Signature: <TOKA_WEBHOOK_SECRET>`

  Body de ejemplo:
  ```json
  {
    "toka_customer_id": "CLI-123",
    "customer_name": "David Pérez",
    "payment_number": "PAY-0001",
    "amount": 1299.00,
    "status": "CONFIRMED",
    "order_id": 5
  }
  ```
  Al confirmarse el pago: se marca el pedido como **PAGADO** y se **descuenta el
  inventario** de sus productos (una sola vez).

---

---

## API Pública para consumidores externos (`/api/public/v1/`)

Capa **aislada** de la API interna, pensada para que empresas externas consuman
datos del catálogo. Es de **solo lectura**, autenticada por **API Key** (no JWT),
versionada y con límite de peticiones por consumidor. No expone usuarios, pagos
ni datos personales de clientes.

### Emitir una API Key a un consumidor externo

Por consola:

```bash
cd backend
.venv\Scripts\Activate.ps1
python manage.py create_api_client "Nombre Empresa Externa" --email contacto@empresa.com --rate 120
```

Devuelve la API Key **una sola vez** (en la base solo se guarda su hash).
También se puede emitir/rotar desde el admin de Django → *Consumidores de API*.

### Uso por el consumidor externo

Se envía la clave en el header `X-API-Key`:

```bash
curl https://TU-DOMINIO/api/public/v1/products/ \
     -H "X-API-Key: tok_xxxxxxxxxxxxxxxxxxxxxxxx"
```

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/public/v1/products/` | Catálogo de productos activos |
| GET | `/api/public/v1/products/<sku>/` | Detalle por SKU |
| GET | `/api/public/v1/categories/` | Categorías activas |
| GET | `/api/public/v1/carousels/` | Carruseles de ads activos |

- Sin clave o clave inválida → **401**.
- Límite configurable por consumidor (`rate_limit_per_min`, por defecto 60/min) → **429** al excederlo.
- La clave se puede **revocar** (desactivar) o **rotar** en cualquier momento desde el admin.

> **Escalabilidad:** el proyecto es un **monolito modular** API-first. Esta app
> `public_api` está desacoplada (auth, permisos y versionado propios), de modo que
> más adelante puede extraerse a un servicio independiente sin reescribir la lógica.

---

## Notas de negocio implementadas

- Las **direcciones de entrega** se guardan por cliente en tabla independiente
  (`orders_customeraddress`) y son **seleccionables y editables** en cada pedido
  (el pedido guarda una copia editable de la dirección).
- El **descuento de inventario** ocurre tras la confirmación del pago desde Toka.
- **Ads:** máximo 4 fotos por carrusel + tamaño (ancho/alto) configurable.
- **Logística inversa** y **Reportes posventa:** estructura base creada; campos
  definitivos quedan pendientes por confirmar (marcados con `TODO`).
