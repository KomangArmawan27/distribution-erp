# ERP Backend — Item Master Module

Asynchronous FastAPI backend for the ERP system's **Item Master** module (`inventory`
schema) and its supporting lookup table (`system` schema).

---

## 1. Tech Stack

| Layer       | Choice                            | Notes                                        |
|-------------|-----------------------------------|----------------------------------------------|
| API         | FastAPI                           | Routers per resource, Pydantic response models |
| ORM         | SQLAlchemy 2.0 (async)            | `DeclarativeBase`, `mapped_column`           |
| DB driver   | asyncpg                           | Runtime (async)                              |
| Migrations  | Alembic                           | Runs sync via psycopg2-binary                |
| Validation  | Pydantic v2                       | `BaseModel`, `field_validator`, generics     |
| Server      | Uvicorn                           | `uvicorn app.main:app --reload`              |
| Config      | pydantic-settings + python-dotenv | `.env` file at project root                  |
| Database    | PostgreSQL 15+ (PostgreSQL 16)    | Schemas: `system`, `inventory`               |

---

## 2. Project Structure

```
idj-erp-be/
├── app/
│   ├── main.py                  # FastAPI entrypoint, middleware, exception handlers
│   ├── config/
│   │   ├── settings.py          # Settings (reads .env)
│   │   └── database.py          # Async engine, AsyncSessionLocal, Base, get_db
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py          # Re-exports Group, Item, ItemPriceList
│   │   ├── group.py             # system.group
│   │   ├── item.py              # inventory.item
│   │   └── item_pricelist.py    # inventory.item_pricelist
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── envelope.py          # Envelope[T], PaginationModel, LinksModel, ErrorModel, MetaModel
│   │   ├── group.py             # GroupCreate / GroupUpdate / GroupRead
│   │   ├── item.py              # ItemCreate / ItemUpdate / ItemRead (+ uppercase mixin)
│   │   └── item_pricelist.py    # ItemPriceListCreate / Update / Read
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── base.py              # Generic CRUD base (incl. page/offset pagination)
│   │   ├── group.py             # group_crud instance + get_group_value resolver
│   │   ├── item.py              # CRUDItem: SKU generation, item_name derivation, group validation
│   │   └── item_pricelist.py    # item_pricelist_crud instance
│   ├── utils/
│   │   ├── pagination.py        # PageResult, compute_page_result, build_links, pagination_dict
│   │   └── response.py          # APIError, success(), error(), meta(), request_id()
│   └── routers/                 # REST endpoints
│       ├── __init__.py
│       ├── group.py             # /groups
│       ├── item.py              # /items
│       └── item_pricelist.py    # /item-pricelist
├── alembic/
│   ├── env.py                   # Loads DATABASE_URL_SYNC dynamically from settings
│   └── versions/
│       ├── 7c67a18f645e_create_inventory_and_system_schemas.py
│       └── 5c9ca3d9408d_create_group_item_item_pricelist_tables.py
├── alembic.ini
├── requirements.txt
├── .env / .env.example
├── pagination.md                # API response & pagination standard (source of truth)
├── error_handling.md            # Error handling standard & code registry
├── DOCUMENTATION.md             # Complete architectural documentation & AI reference
└── README.md
```

---

## 3. Setup

### Requirements

```bash
pip install -r requirements.txt
```

### Environment — `.env`

Copy `.env.example` to `.env` and set credentials. Both URL lines must match your
real user/password (the `POSTGRES_*` vars are not auto-assembled):

```env
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=changeme
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=erp_db

DATABASE_URL=postgresql+asyncpg://erp_user:changeme@localhost:5432/erp_db
DATABASE_URL_SYNC=postgresql+psycopg2://erp_user:changeme@localhost:5432/erp_db

APP_ENV=development
```

### Database

Create the role and database (as a DB superuser):

```sql
CREATE USER erp_user WITH PASSWORD 'changeme';
CREATE DATABASE erp_db OWNER erp_user;
```

### Migrations

```bash
alembic upgrade head          # creates schemas + tables
alembic downgrade -1          # rollback one step
```

- Migration 1 (`7c67a18f645e`): creates `inventory` and `system` schemas.
- Migration 2 (`5c9ca3d9408d`): creates `system.group`, `inventory.item`, and `inventory.item_pricelist`.

---

## 4. Run

```bash
uvicorn app.main:app --reload
```

Interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 5. Database Design

### `system.group` — generic lookup table

One physical table, partitioned logically by `group_name` (e.g. `SUB GROUP`,
`BRAND GROUP`, `SERIES GROUP`, `PACK GROUP`, `ML GROUP`, `NIC GROUP`).

| Column      | Type         | Constraints                                       |
|-------------|--------------|---------------------------------------------------|
| group_id    | SERIAL       | Primary key                                       |
| group_noid  | SMALLINT     | Not null, unique within a `group_name`            |
| group_name  | VARCHAR(50)  | Not null, lookup category                         |
| group_value | VARCHAR(100) | Not null, display value (stored uppercase)        |

Constraint: `UNIQUE (group_name, group_noid)`.

### `inventory.item` — item master

`*_group` columns store `group_noid`. Referential integrity is enforced at the
application layer: joins resolve the value by filtering on `group_name`
(e.g. `WHERE group_name = 'BRAND GROUP' AND group_noid = <noid>`).

| Column        | Type         | Constraints / Notes                                                |
|---------------|--------------|--------------------------------------------------------------------|
| item_id       | SERIAL       | Primary key                                                        |
| item_no       | VARCHAR(50)  | SKU, UNIQUE; auto-generated if omitted (see §6)                    |
| item_name     | VARCHAR(255) | Derived: sub + brand + series + flavour + pack + ml + nic (see §6) |
| sub_group     | SMALLINT     | Nullable, `group_noid` → `system.group` (SUB GROUP)                |
| brand_group   | SMALLINT     | Nullable, `group_noid` → `system.group` (BRAND GROUP)              |
| series_group  | SMALLINT     | Nullable, `group_noid` → `system.group` (SERIES GROUP)             |
| flavour_group | VARCHAR(100) | Nullable, free text, automatically uppercased                      |
| pack_group    | SMALLINT     | Nullable, `group_noid` → `system.group` (PACK GROUP)               |
| ml_group      | SMALLINT     | Nullable, `group_noid` → `system.group` (ML GROUP)                 |
| nic_group     | SMALLINT     | Nullable, `group_noid` → `system.group` (NIC GROUP)                |
| item_year     | INT          | Nullable, e.g. 2026                                                |

### `inventory.item_pricelist`

| Column            | Type          | Constraints / Notes                                                |
|-------------------|---------------|--------------------------------------------------------------------|
| id                | SERIAL        | Primary key                                                        |
| item_id           | INT           | Not null, FK → `inventory.item(item_id)` ON DELETE CASCADE, UNIQUE |
| item_price_ms     | NUMERIC(12,2) | Not null, market/retail selling price                              |
| item_price_ws     | NUMERIC(12,2) | Not null, wholesale price                                          |
| item_price_distri | NUMERIC(12,2) | Not null, distributor price                                        |

---

## 6. Domain Logic & Business Rules

### 6.1 `item_no` auto-generation

When creating an item without `item_no` (or sending `null`/empty), the system generates it as:

```
LEFT(flavour_group, 3).upper() + 4-digit zero-padded counter
```

Example: creating items with `flavour_group = "Strawberry"` produces `STR0001`, `STR0002`, etc.
The counter increments per matching flavour (case-insensitive). If `flavour_group` is also missing, a 422 `VALIDATION_ERROR` is returned.

### 6.2 `item_name` derivation

`item_name` is computed on create and update by joining the resolved group values in order, separated by a single space (no separators):

```
sub_group brand_group series_group flavour_group pack_group ml_group nic_group
```

Example: `SALTNIC BLONDIES MASTERPIECE SERIES MATCHA 15 ML 3 MG`

### 6.3 Input normalization (uppercase)

`app/schemas/item.py` uses `_UppercaseMixin` to automatically strip and uppercase `flavour_group` and `item_no` on both create and update operations.

### 6.4 Pre-write relational & integrity guards

- **Group duplicate check** (`app/routers/group.py`): `POST /groups/` and `PUT /groups/{id}` verify that the `(group_name, group_noid)` pair is not already taken, returning **409 `GROUP_NOID_TAKEN`** before hitting the database unique constraint.
- **Item group reference check** (`app/routers/item.py`): `POST /items/` and `PUT /items/{id}` verify that all supplied `*_group` noids exist in `system.group`, returning **404 `GROUP_NOT_FOUND`** if any referenced group does not exist.
- **Pricelist item existence check** (`app/routers/item_pricelist.py`): `POST /item-pricelist/` and `PUT /item-pricelist/{id}` verify that `item_id` exists in `inventory.item`, returning **404 `ITEM_NOT_FOUND`** instead of raising a database integrity error.

---

## 7. API Conventions & Error Handling

Every endpoint follows the standard response envelope (see `pagination.md` and `error_handling.md`).

### Envelope fields

- `success` (bool, always present)
- `message` (string, human-readable)
- `data` (array, object, or `null`)
- `pagination` (object, present only on paginated list responses)
- `links` (object with `self`, `next`, `prev`, present only on paginated list responses)
- `error` (`{ "code": "...", "details": ... }`, present only on error responses)
- `meta` (`{ "timestamp": "...", "request_id": "req_..." }`, always present)

### Stable error codes

| Code               | HTTP | Triggered When                                                            |
|--------------------|------|----------------------------------------------------------------------------|
| `GROUP_NOT_FOUND`   | 404  | `group_id` not found; or an item references a non-existent group noid      |
| `GROUP_NOID_TAKEN`  | 409  | Creating/updating a group with a `(group_name, group_noid)` already in use |
| `ITEM_NOT_FOUND`    | 404  | `item_id` not found; or pricelist references a missing item                |
| `PRICE_NOT_FOUND`   | 404  | Pricelist record `id` not found                                            |
| `VALIDATION_ERROR`  | 422  | Pydantic validation failure; missing flavour when SKU generation needed   |
| `INTERNAL_ERROR`    | 500  | Unhandled server exception                                                 |

---

## 8. Pagination (Offset / Page-Based)

All list endpoints (`/groups/`, `/items/`, `/item-pricelist/`) use offset/page-based pagination ordered by primary key descending (`ORDER BY pk DESC`).

### Query parameters

| Param      | Default | Constraints          | Behavior                                    |
|------------|---------|----------------------|---------------------------------------------|
| `page`     | 1       | `ge=1`               | 1-based page number                         |
| `per_page` | 20      | `ge=1, le=100`       | `> 100` returns 422 `VALIDATION_ERROR`      |

### Pagination response object

```json
{
  "page": 1,
  "per_page": 20,
  "total_items": 5,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false
}
```

---

## 9. Endpoints Summary

| Method | Path                         | Description                                            |
|--------|------------------------------|--------------------------------------------------------|
| GET    | `/health`                    | Service health check                                   |
| GET    | `/groups/`                   | List groups (`?group_name=&page=1&per_page=20`)        |
| POST   | `/groups/`                   | Create group (guards against duplicate `group_noid`)   |
| GET    | `/groups/{group_id}`         | Get group by ID                                        |
| PUT    | `/groups/{group_id}`         | Update group                                           |
| DELETE | `/groups/{group_id}`         | Delete group (204 No Content)                          |
| GET    | `/items/`                    | List items (paginated)                                 |
| POST   | `/items/`                    | Create item (auto-generates `item_no` and `item_name`) |
| GET    | `/items/{item_id}`           | Get item by ID                                         |
| PUT    | `/items/{item_id}`           | Update item (recomputes `item_name`)                   |
| DELETE | `/items/{item_id}`           | Delete item (204 No Content)                           |
| GET    | `/item-pricelist/`           | List price records (paginated)                         |
| POST   | `/item-pricelist/`           | Create price record (validates `item_id` exists)       |
| GET    | `/item-pricelist/{price_id}` | Get price record by ID                                 |
| PUT    | `/item-pricelist/{price_id}` | Update price record                                    |
| DELETE | `/item-pricelist/{price_id}` | Delete price record (204 No Content)                   |

### Example — Create Item (Auto SKU & Derived Name)

```bash
curl -X POST http://localhost:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{
    "sub_group": 2,
    "brand_group": 1,
    "series_group": 1,
    "flavour_group": "Matcha",
    "ml_group": 1,
    "nic_group": 1,
    "item_year": 2026
  }'
```

Response `data`:

```json
{
  "item_id": 3,
  "item_no": "MAT0001",
  "item_name": "SALTNIC BLONDIES MASTERPIECE SERIES MATCHA 15 ML 3 MG",
  "sub_group": 2,
  "brand_group": 1,
  "series_group": 1,
  "flavour_group": "MATCHA",
  "pack_group": null,
  "ml_group": 1,
  "nic_group": 1,
  "item_year": 2026
}
```
