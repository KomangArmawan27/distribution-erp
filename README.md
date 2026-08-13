# ERP Backend — Item Master Module

Asynchronous FastAPI backend for the ERP system's **Item Master** module (`inventory`
schema) and its supporting lookup table (`system` schema).

---

## 1. Tech Stack

| Layer       | Choice                            |
|-------------|-----------------------------------|
| API         | FastAPI                           |
| ORM         | SQLAlchemy 2.0 (async)            |
| DB driver   | asyncpg                           |
| Migrations  | Alembic (sync via psycopg2)       |
| Validation  | Pydantic v2                       |
| Server      | Uvicorn                           |
| Config      | pydantic-settings + python-dotenv |
| Database    | PostgreSQL 15+                    |

---

## 2. Project Structure

```
erp-backend/
├── app/
│   ├── main.py                  # FastAPI app entrypoint, middleware, exception handlers
│   ├── config/
│   │   ├── settings.py          # Settings (reads .env)
│   │   └── database.py          # Async engine, session, Base
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── group.py             # system.group
│   │   ├── item.py              # inventory.item
│   │   └── item_pricelist.py    # inventory.item_pricelist
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── envelope.py          # Standard response envelope
│   │   ├── group.py
│   │   ├── item.py
│   │   └── item_pricelist.py
│   ├── crud/
│   │   ├── base.py              # Generic CRUD base (incl. page/offset)
│   │   ├── group.py             # get_group_value resolver
│   │   ├── item.py              # item_crud + item_name/item_no generation
│   │   └── item_pricelist.py
│   ├── utils/
│   │   ├── pagination.py        # PageResult, links, pagination_dict
│   │   └── response.py          # success/error builders, APIError
│   └── routers/                 # REST endpoints
│       ├── group.py             # /groups
│       ├── item.py              # /items
│       └── item_pricelist.py    # /item-pricelist
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── requirements.txt
├── .env.example
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

The first migration creates the `inventory` and `system` schemas; the second
creates `system.group`, `inventory.item`, and `inventory.item_pricelist`.

---

## 4. Run

```bash
uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs (Swagger UI) or http://localhost:8000/redoc.

---

## 5. Database Design

### `system.group` — generic lookup table

One physical table, partitioned logically by `group_name` (e.g. `SUB GROUP`,
`BRAND GROUP`, `SERIES GROUP`, `PACK GROUP`, `ML GROUP`, `NIC GROUP`).

| Column      | Type         | Notes                                     |
|-------------|--------------|-------------------------------------------|
| group_id    | SERIAL PK    | Primary key                               |
| group_noid  | SMALLINT     | Local id, unique only *within* a group    |
| group_name  | VARCHAR(50)  | Lookup category                           |
| group_value | VARCHAR(100) | Display value                             |

`UNIQUE (group_name, group_noid)`.

### `inventory.item` — item master

`*_group` columns store `group_noid`. Referential integrity is enforced at the
application layer: joins resolve the value by filtering on `group_name`
(e.g. `WHERE group_name = 'BRAND GROUP' AND group_noid = <noid>`).

| Column        | Type            | Notes                                            |
|---------------|-----------------|---------------------------------------------------|
| item_id       | SERIAL PK       | Auto increment                                    |
| item_no       | VARCHAR(50)     | SKU, UNIQUE; auto-generated if omitted (see §6)   |
| item_name     | VARCHAR(255)    | Derived: sub + brand + series + flavour + pack + ml + nic (see §6) |
| sub_group     | SMALLINT        | group_noid → `system.group` (SUB GROUP)           |
| brand_group   | SMALLINT        | group_noid → `system.group` (BRAND GROUP)         |
| series_group  | SMALLINT        | group_noid → `system.group` (SERIES GROUP)        |
| flavour_group | VARCHAR(100)    | Free text, no lookup                              |
| pack_group    | SMALLINT        | group_noid → `system.group` (PACK GROUP)          |
| ml_group      | SMALLINT        | group_noid → `system.group` (ML GROUP)            |
| nic_group     | SMALLINT        | group_noid → `system.group` (NIC GROUP)           |
| item_year     | INT             | e.g. 2026                                         |

### `inventory.item_pricelist`

| Column            | Type          | Notes                                       |
|-------------------|---------------|---------------------------------------------|
| id                | SERIAL PK     | Auto increment                              |
| item_id           | INT FK        | → `inventory.item(item_id)` (0..n history)  |
| item_price_ms     | NUMERIC(12,2) | Market/retail selling price                 |
| item_price_ws     | NUMERIC(12,2) | Wholesale price                             |
| item_price_distri | NUMERIC(12,2) | Distributor price                           |

---

## 6. `item_no` and `item_name`

Both are computed in the app layer (`app/crud/item.py`).

### `item_no` auto-generation

When the request body omits `item_no` (or sends empty/`null`), it is generated as:

```
LEFT(flavour_group, 3).upper() + 4-digit zero-padded per-flavour counter
```

Example: creating items with `flavour_group = "Strawberry"` produces
`STR0001`, `STR0002`, … The counter increases per matching flavour (case-insensitive).
If `flavour_group` is also missing, a 422 `VALIDATION_ERROR` is returned.

### `item_name` derivation

`item_name` joins the resolved group values in order, single-space separated:

```
sub_group value, brand value, series value, flavour text, pack value, ml value, nic value
```

Example: `SALTNIC BLONDIES MASTERPIECE SERIES Matcha 15 ML 3 MG`

The `*_group` noids are resolved against `system.group` at create/update time;
an unknown `(group_name, group_noid)` pair fails with 422.

---

## 7. API Conventions

Every endpoint follows the standard response envelope (see `pagination.md`):

- `success` — boolean, always present
- `message` — human-readable summary
- `data` — array (list) or object (single), `null` on error
- `pagination` — present on list endpoints only
- `links` — self/next/prev, present on list endpoints only
- `error` — `{ code, details }`, present on error responses only
- `meta` — `{ timestamp, request_id }`, always present

`request_id` is generated per-request by middleware and used for log correlation.
Stable error codes: `GROUP_NOT_FOUND`, `ITEM_NOT_FOUND`, `PRICE_NOT_FOUND`,
`VALIDATION_ERROR`, `INTERNAL_ERROR`, etc.

### Pagination (offset/page-based)

| Param     | Default | Max | Notes                          |
|-----------|---------|-----|--------------------------------|
| `page`    | 1       | -   | 1-based                        |
| `per_page`| 20      | 100 | `> 100` → 422 `VALIDATION_ERROR` |

`pagination` object (see `app/utils/pagination.py`):

```json
{
  "page": 1,
  "per_page": 20,
  "total_items": 532,
  "total_pages": 27,
  "has_next": true,
  "has_prev": false
}
```

Request: `GET /items?page=2&per_page=20`

---

## 8. Endpoints

| Method | Path                          | Description                    |
|--------|-------------------------------|--------------------------------|
| GET    | `/health`                     | Liveness check                 |
| GET    | `/groups/`                    | List groups (`?group_name=`)   |
| POST   | `/groups/`                    | Create group                   |
| GET    | `/groups/{group_id}`          | Get group                      |
| PUT    | `/groups/{group_id}`          | Update group                   |
| DELETE | `/groups/{group_id}`          | Delete group (204)             |
| GET    | `/items/`                     | List items (paginated)         |
| POST   | `/items/`                     | Create item                    |
| GET    | `/items/{item_id}`            | Get item                       |
| PUT    | `/items/{item_id}`            | Update item                    |
| DELETE | `/items/{item_id}`            | Delete item (204)              |
| GET    | `/item-pricelist/`            | List price records (paginated) |
| POST   | `/item-pricelist/`            | Create price record            |
| GET    | `/item-pricelist/{price_id}`  | Get price record               |
| PUT    | `/item-pricelist/{price_id}`  | Update price record            |
| DELETE | `/item-pricelist/{price_id}`  | Delete price record (204)      |

### Example — create an item (auto SKU)

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

Response `data` (abridged):

```json
{
  "item_id": 1,
  "item_no": "MAT0001",
  "item_name": "SALTNIC BLONDIES MASTERPIECE SERIES Matcha 15 ML 3 MG",
  "sub_group": 2,
  "brand_group": 1,
  "series_group": 1,
  "flavour_group": "Matcha",
  "ml_group": 1,
  "nic_group": 1,
  "item_year": 2026
}
```

---

## 9. Development Notes

- `APP_ENV=development` enables SQL echo on the async engine.
- Generic CRUD lives in `app/crud/base.py`; per-table instances are one-liners
  (`app/crud/group.py`, `app/crud/item_pricelist.py`).
- Cursor-based pagination was the previous default; the project now uses
  offset/page-based pagination (see `app/utils/pagination.py`). See `pagination.md`
  §5 for guidance on choosing the right style per endpoint.