# ERP Backend — Item, HR, Sales, & Sales Order Modules

Asynchronous FastAPI backend for the ERP system's **Item Master** (`inventory` schema), **HR** (`hr` schema), **Sales** (`sales` schema), and supporting lookup tables (`system` schema).

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
| Database    | PostgreSQL 15+ (PostgreSQL 16)    | Schemas: `system`, `inventory`, `hr`, `sales`|

---

## 2. Project Structure

```
idj-erp-be/
├── app/
│   ├── main.py                  # FastAPI entrypoint, middleware, exception handlers
│   ├── core/                    # Shared core infrastructure & utilities
│   │   ├── config.py            # Settings (reads .env)
│   │   ├── database.py          # Async engine, AsyncSessionLocal, Base, get_db
│   │   ├── base_crud.py         # Generic CRUD base (incl. page/offset pagination & .unique())
│   │   ├── envelope.py          # Envelope[T], PaginationModel, LinksModel, ErrorModel, MetaModel
│   │   ├── pagination.py        # PageResult, compute_page_result, build_links, pagination_dict
│   │   └── response.py          # APIError, success(), error(), meta(), request_id()
│   └── modules/                 # Domain-based feature modules
│       ├── group/               # system.group (models, schemas, crud, router)
│       ├── item/                # inventory.item (models, schemas, crud, router)
│       ├── item_pricelist/      # inventory.item_pricelist (models, schemas, crud, router)
│       ├── employee/            # hr.employee (models, schemas, crud, router)
│       ├── sales_person/        # sales.sales_person (models, schemas, crud, router)
│       ├── customer/            # sales.customer (models, schemas, crud, router)
│       └── sales_order/         # sales.order_header & order_detail (models, schemas, crud, router)
├── alembic/
│   ├── env.py                   # Loads DATABASE_URL_SYNC dynamically from settings
│   └── versions/                # Alembic migration revisions
├── alembic.ini
├── requirements.txt
├── .env / .env.example
├── customer_top.md              # Customer Terms of Payment module specs
├── sales_order_schema.md        # Sales Order module specs
└── README.md
```

---

## 3. Setup

### Requirements

```bash
pip install -r requirements.txt
```

### Environment — `.env`

Copy `.env.example` to `.env` and set credentials:

```env
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=erp_db

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/erp_db
DATABASE_URL_SYNC=postgresql+psycopg2://user:password@localhost:5432/erp_db

APP_ENV=development
```

### Migrations & Seeding

```bash
alembic upgrade head          # creates schemas + tables & applies all migrations
python scripts/seed_groups.py # populates system lookup groups
alembic downgrade -1          # rollback one step
```

- Migration 1 (`7c67a18f645e`): creates `inventory` and `system` schemas.
- Migration 2 (`5c9ca3d9408d`): creates `system.group`, `inventory.item`, and `inventory.item_pricelist`.
- Migration 3 (`63b865b5ada5`): renames `id` to `pricelist_id` in `inventory.item_pricelist`.
- Migration 4 (`ed7260bbaf85`): creates `hr` and `sales` schemas and tables (`hr.employee`, `sales.sales_person`, `sales.customer`).
- Migration 5 (`2781c4f12188`): adds `customer_top` and composite FK to `sales.customer`.
- Migration 6 (`98a7b6c5d4e3`): renames `system.group.group_value` to `group_display` and adds integer `group_value` for day-offset calculations.
- Migration 7 (`39a8b7c6d5e4`): creates `sales.order_header` and `sales.order_detail`.
- **Seeder Script (`scripts/seed_groups.py`)**: scans group mappings and idempotently populates `system.group` with display labels and integer day-offset values.

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
One physical table, partitioned logically by `group_name`.

| Column          | Type         | Constraints / Notes                                        |
|-----------------|--------------|------------------------------------------------------------|
| group_id        | SERIAL       | Primary key, autoincrement                                 |
| group_noid      | SMALLINT     | Not null, unique within a `group_name`                     |
| group_name      | VARCHAR(50)  | Not null, lookup category                                  |
| group_display   | VARCHAR(100) | Not null, display text (e.g. `NET 15`, `ACTIVE`, `STAFF`)  |
| group_value     | INTEGER      | Nullable, integer value / day-offset (e.g. `15` for NET 15)|

### `inventory.item` — Item Master
Item master data.

| Column          | Type         | Constraints / Notes                                        |
|-----------------|--------------|------------------------------------------------------------|
| item_id         | SERIAL       | Primary key, autoincrement                                 |
| item_no         | VARCHAR(50)  | Not null, unique SKU / item number                         |
| item_name       | VARCHAR(255) | Not null, derived item description                         |
| sub_group       | SMALLINT     | Nullable, FK reference to `system.group` (`SUB GROUP`)     |
| brand_group     | SMALLINT     | Nullable, FK reference to `system.group` (`BRAND GROUP`)   |
| series_group    | SMALLINT     | Nullable, FK reference to `system.group` (`SERIES GROUP`)  |
| flavour_group   | VARCHAR(100) | Nullable, flavour specification                            |
| pack_group      | SMALLINT     | Nullable, FK reference to `system.group` (`PACK GROUP`)    |
| ml_group        | SMALLINT     | Nullable, FK reference to `system.group` (`ML GROUP`)      |
| nic_group       | SMALLINT     | Nullable, FK reference to `system.group` (`NIC GROUP`)     |
| item_year       | INTEGER      | Nullable, item release year                                |

### `inventory.item_pricelist` — Item Pricelist
Pricelist records per item.

| Column          | Type         | Constraints / Notes                                        |
|-----------------|--------------|------------------------------------------------------------|
| pricelist_id    | SERIAL       | Primary key, autoincrement                                 |
| item_id         | INTEGER      | FK -> `inventory.item(item_id)` (on delete CASCADE), unique|
| item_price_ms   | NUMERIC(12,2)| Not null, Modern Market / MS price                         |
| item_price_ws   | NUMERIC(12,2)| Not null, Wholesale / WS price                             |
| item_price_distri| NUMERIC(12,2)| Not null, Distributor price                               |

### `hr.employee` — HR Employee Table
Employee records.

| Column          | Type         | Constraints / Notes                                        |
|-----------------|--------------|------------------------------------------------------------|
| employee_id     | SERIAL       | Primary key, autoincrement                                 |
| employee_no     | VARCHAR(50)  | Not null, unique employee number                           |
| employee_name   | VARCHAR(255) | Not null, employee full name                               |
| position        | SMALLINT     | Nullable, FK reference to `system.group` (`POSITION`)      |
| department      | SMALLINT     | Nullable, FK reference to `system.group` (`DEPARTMENT`)    |
| join_date       | DATE         | Nullable, employee join date                               |
| status          | SMALLINT     | Nullable, FK reference to `system.group` (`STATUS`)        |

### `sales.sales_person` — Sales Person Table
Sales personnel mapping to employees.

| Column          | Type         | Constraints / Notes                                        |
|-----------------|--------------|------------------------------------------------------------|
| sales_person_id | SERIAL       | Primary key, autoincrement                                 |
| employee_id     | INTEGER      | FK -> `hr.employee(employee_id)` (on delete CASCADE), not null|
| sales_person_no | VARCHAR(50)  | Not null, unique sales person number                       |
| sales_area      | SMALLINT     | Nullable, FK reference to `system.group` (`SALES AREA`)    |
| sales_level     | SMALLINT     | Nullable, FK reference to `system.group` (`SALES LEVEL`)   |
| status          | SMALLINT     | Nullable, FK reference to `system.group` (`STATUS`)        |

### `sales.customer` — Customer Table
Customer master records.

| Column          | Type         | Constraints / Notes                                        |
|-----------------|--------------|------------------------------------------------------------|
| customer_id     | SERIAL       | Primary key, autoincrement                                 |
| customer_no     | VARCHAR(50)  | Not null, unique customer number                           |
| customer_name   | VARCHAR(255) | Not null, customer company/name                            |
| customer_type   | SMALLINT     | Nullable, FK reference to `system.group` (`CUSTOMER TYPE`) |
| customer_top    | SMALLINT     | Nullable, FK reference to `system.group` (`CUSTOMER TOP`)  |
| sales_person_id | INTEGER      | FK -> `sales.sales_person(sales_person_id)` (on delete SET NULL), nullable |
| address         | VARCHAR(500) | Nullable, customer address                                 |
| city_region     | SMALLINT     | Nullable, FK reference to `system.group` (`CITY REGION`)   |
| phone           | VARCHAR(50)  | Nullable, customer phone number                            |
| status          | SMALLINT     | Nullable, FK reference to `system.group` (`STATUS`)        |

### `sales.order_header` — Sales Order Header
Sales order document headers.

| Column          | Type         | Constraints / Notes                                        |
|-----------------|--------------|------------------------------------------------------------|
| doc_id          | SERIAL       | Primary key, autoincrement                                 |
| doc_no          | VARCHAR(50)  | Not null, unique document number (`SOYYMM0001`)            |
| doc_date        | DATE         | Not null, order date                                       |
| doc_duedate     | DATE         | Not null, auto-calculated payment due date (day-offset)    |
| doc_terms       | SMALLINT     | Not null, FK reference to `system.group` (`CUSTOMER TOP`)  |
| cust_id         | INTEGER      | FK -> `sales.customer(customer_id)` (on delete RESTRICT), not null |
| dropship_id     | INTEGER      | FK -> `sales.customer(customer_id)` (on delete SET NULL), nullable |
| sales_id        | INTEGER      | FK -> `sales.sales_person(sales_person_id)` (on delete SET NULL), nullable |

### `sales.order_detail` — Sales Order Detail
Sales order line items.

| Column          | Type         | Constraints / Notes                                        |
|-----------------|--------------|------------------------------------------------------------|
| trans_id        | SERIAL       | Primary key, autoincrement                                 |
| doc_id          | INTEGER      | FK -> `sales.order_header(doc_id)` (on delete CASCADE), not null |
| trans_idx       | INTEGER      | Not null, line sequence number per order                   |
| item_id         | INTEGER      | FK -> `inventory.item(item_id)` (on delete RESTRICT), not null |
| trans_qty       | INTEGER      | Not null, transaction quantity (`> 0`)                     |
| trans_price     | NUMERIC(15,2)| Not null, unit price snapshot                              |
| trans_total     | NUMERIC(15,2)| Not null, line total (`trans_qty * trans_price`)           |

---

## 6. Group Display Lookups (`*_display`)

All GET endpoints automatically batch-resolve foreign-key group `noid` references from `system.group` into corresponding `*_display` fields (e.g. `doc_terms_display`, `position_display`, `customer_top_display`, etc.).

---

## 7. Endpoints Summary

| Method | Path                         | Description                                            |
|--------|------------------------------|--------------------------------------------------------|
| GET    | `/health`                    | Service health check                                   |
| GET    | `/groups/`                   | List groups                                            |
| POST   | `/groups/`                   | Create group (guards against duplicate `group_noid`)   |
| GET    | `/groups/{group_id}`         | Get group by ID                                        |
| PUT    | `/groups/{group_id}`         | Update group                                           |
| DELETE | `/groups/{group_id}`         | Delete group                                           |
| GET    | `/items/`                    | List items (paginated, with group displays)            |
| POST   | `/items/`                    | Create item (auto SKU & derived name)                  |
| GET    | `/items/{item_id}`           | Get item by ID                                         |
| PUT    | `/items/{item_id}`           | Update item                                            |
| DELETE | `/items/{item_id}`           | Delete item                                            |
| GET    | `/item-pricelist/`           | List price records (paginated, with item details)      |
| POST   | `/item-pricelist/`           | Create price record (validates `item_id` exists)       |
| GET    | `/item-pricelist/{pricelist_id}` | Get price record by ID                             |
| PUT    | `/item-pricelist/{pricelist_id}` | Update price record                                |
| DELETE | `/item-pricelist/{pricelist_id}` | Delete price record                                |
| GET    | `/employees/`                | List employees (paginated, with group displays)        |
| POST   | `/employees/`                | Create employee                                        |
| GET    | `/employees/{employee_id}`   | Get employee by ID                                     |
| PUT    | `/employees/{employee_id}`   | Update employee                                        |
| DELETE | `/employees/{employee_id}`   | Delete employee                                        |
| GET    | `/sales-persons/`            | List sales persons (paginated, with group displays)    |
| POST   | `/sales-persons/`            | Create sales person                                    |
| GET    | `/sales-persons/{sales_person_id}` | Get sales person by ID                           |
| PUT    | `/sales-persons/{sales_person_id}` | Update sales person                            |
| DELETE | `/sales-persons/{sales_person_id}` | Delete sales person                            |
| GET    | `/customers/`                | List customers (paginated, with group displays)        |
| POST   | `/customers/`                | Create customer                                        |
| GET    | `/customers/{customer_id}`   | Get customer by ID                                     |
| PUT    | `/customers/{customer_id}`   | Update customer                                        |
| DELETE | `/customers/{customer_id}`   | Delete customer                                        |
| GET    | `/sales-orders/`             | List sales orders (paginated, with details & displays) |
| POST   | `/sales-orders/`             | Create sales order (auto doc_no, doc_duedate, totals)  |
| GET    | `/sales-orders/{doc_id}`     | Get sales order by ID with details                     |
| PUT    | `/sales-orders/{doc_id}`     | Update sales order                                     |
| DELETE | `/sales-orders/{doc_id}`     | Delete sales order                                     |
