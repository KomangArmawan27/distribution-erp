# ERP Backend — Item, HR, & Sales Master Modules

Asynchronous FastAPI backend for the ERP system's **Item Master** (`inventory` schema), **HR & Sales** modules (`hr` and `sales` schemas), and supporting lookup tables (`system` schema).

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
distribution-erp/
├── app/
│   ├── main.py                  # FastAPI entrypoint, middleware, exception handlers
│   ├── config/
│   │   ├── settings.py          # Settings (reads .env)
│   │   └── database.py          # Async engine, AsyncSessionLocal, Base, get_db
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py          # Re-exports all models
│   │   ├── group.py             # system.group
│   │   ├── item.py              # inventory.item
│   │   ├── item_pricelist.py    # inventory.item_pricelist
│   │   ├── employee.py          # hr.employee
│   │   ├── sales_person.py      # sales.sales_person
│   │   └── customer.py          # sales.customer
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── envelope.py          # Envelope[T], PaginationModel, LinksModel, ErrorModel, MetaModel
│   │   ├── group.py             # GroupCreate / GroupUpdate / GroupRead
│   │   ├── item.py              # ItemCreate / ItemUpdate / ItemRead (+ group display fields)
│   │   ├── item_pricelist.py    # ItemPriceListCreate / Update / Read
│   │   ├── employee.py          # EmployeeCreate / Update / Read
│   │   ├── sales_person.py      # SalesPersonCreate / Update / Read
│   │   └── customer.py          # CustomerCreate / Update / Read
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── base.py              # Generic CRUD base (incl. page/offset pagination)
│   │   ├── group.py             # group_crud instance + get_group_value & populate_group_displays
│   │   ├── item.py              # CRUDItem: SKU generation, item_name derivation, group lookup population
│   │   ├── item_pricelist.py    # item_pricelist_crud instance (joinedload item)
│   │   ├── employee.py          # employee_crud instance + group display population
│   │   ├── sales_person.py      # sales_person_crud instance + group display population
│   │   └── customer.py          # customer_crud instance + group display population
│   ├── utils/
│   │   ├── pagination.py        # PageResult, compute_page_result, build_links, pagination_dict
│   │   └── response.py          # APIError, success(), error(), meta(), request_id()
│   └── routers/                 # REST endpoints
│       ├── __init__.py
│       ├── group.py             # /groups
│       ├── item.py              # /items
│       ├── item_pricelist.py    # /item-pricelist
│       ├── employee.py          # /employees
│       ├── sales_person.py      # /sales-persons
│       └── customer.py          # /customers
├── alembic/
│   ├── env.py                   # Loads DATABASE_URL_SYNC dynamically from settings
│   └── versions/
│       ├── 7c67a18f645e_create_inventory_and_system_schemas.py
│       ├── 5c9ca3d9408d_create_group_item_item_pricelist_tables.py
│       ├── 63b865b5ada5_rename_id_to_pricelist_id_in_item_.py
│       └── ed7260bbaf85_create_hr_and_sales_schemas_and_tables.py
├── alembic.ini
├── requirements.txt
├── .env / .env.example
├── sales_master.md              # Sales & HR master schema specs
├── pagination.md                # API response & pagination standard
├── error_handling.md            # Error handling standard & code registry
└── README.md
```

---

## 3. Setup

### Requirements

```bash
pip install -r requirements.txt
```

### Environment — `.env`

Copy `.env.example` to `.env` and set credentials. Both URL lines must match your real user/password:

```env
POSTGRES_USER=komang
POSTGRES_PASSWORD=damedane098
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=erp_db

DATABASE_URL=postgresql+asyncpg://komang:damedane098@localhost:5432/erp_db
DATABASE_URL_SYNC=postgresql+psycopg2://komang:damedane098@localhost:5432/erp_db

APP_ENV=development
```

### Migrations & Seeding

```bash
alembic upgrade head          # creates schemas + tables & applies all migrations
python scripts/seed_groups.py # populates system lookup groups (Item Master, Employee, Customer, Sales Person)
alembic downgrade -1          # rollback one step
```

- Migration 1 (`7c67a18f645e`): creates `inventory` and `system` schemas.
- Migration 2 (`5c9ca3d9408d`): creates `system.group`, `inventory.item`, and `inventory.item_pricelist`.
- Migration 3 (`63b865b5ada5`): renames `id` to `pricelist_id` in `inventory.item_pricelist`.
- Migration 4 (`ed7260bbaf85`): creates `hr` and `sales` schemas and tables (`hr.employee`, `sales.sales_person`, `sales.customer`).
- **Seeder Script (`scripts/seed_groups.py`)**: scans all group mappings across the application modules and idempotently populates `system.group` with required lookup values.

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
One physical table, partitioned logically by `group_name` (e.g. `SUB GROUP`, `BRAND GROUP`, `SERIES GROUP`, `PACK GROUP`, `ML GROUP`, `NIC GROUP`, `EMPLOYEE POSITION`, `EMPLOYEE DEPARTMENT`, `EMPLOYEE STATUS`, `SALES AREA`, `SALES LEVEL`, `CUSTOMER TYPE`, `CUSTOMER REGION`, `CUSTOMER STATUS`).

| Column      | Type         | Constraints                                       |
|-------------|--------------|---------------------------------------------------|
| group_id    | SERIAL       | Primary key                                       |
| group_noid  | SMALLINT     | Not null, unique within a `group_name`            |
| group_name  | VARCHAR(50)  | Not null, lookup category                         |
| group_value | VARCHAR(100) | Not null, display value                           |

### `inventory.item` — item master
| Column        | Type         | Constraints / Notes                                                |
|---------------|--------------|--------------------------------------------------------------------|
| item_id       | SERIAL       | Primary key                                                        |
| item_no       | VARCHAR(50)  | SKU, UNIQUE; auto-generated if omitted                             |
| item_name     | VARCHAR(255) | Derived: sub + brand + series + flavour + pack + ml + nic          |
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
| pricelist_id      | SERIAL        | Primary key                                                        |
| item_id           | INT           | Not null, FK → `inventory.item(item_id)` ON DELETE CASCADE, UNIQUE |
| item_price_ms     | NUMERIC(12,2) | Not null, market/retail selling price                              |
| item_price_ws     | NUMERIC(12,2) | Not null, wholesale price                                          |
| item_price_distri | NUMERIC(12,2) | Not null, distributor price                                        |

### HR & Sales Tables (`hr.employee`, `sales.sales_person`, `sales.customer`)
- **`hr.employee`**: `employee_id`, `employee_no`, `employee_name`, `position`, `department`, `join_date`, `status`.
- **`sales.sales_person`**: `sales_person_id`, `employee_id`, `sales_person_no`, `sales_area`, `sales_level`, `status`.
- **`sales.customer`**: `customer_id`, `customer_no`, `customer_name`, `customer_type`, `sales_person_id`, `address`, `city_region`, `phone`, `status`.

---

## 6. Group Display Lookups (`*_display`)
All GET endpoints for Item, Employee, Sales Person, and Customer automatically batch-resolve foreign-key group `noid` references from `system.group` into corresponding `*_display` fields (e.g. `sub_group_display`, `position_display`, `customer_type_display`, etc.).

---

## 7. Endpoints Summary

| Method | Path                         | Description                                            |
|--------|------------------------------|--------------------------------------------------------|
| GET    | `/health`                    | Service health check                                   |
| GET    | `/groups/`                   | List groups                                            |
| POST   | `/groups/`                   | Create group                                           |
| GET    | `/groups/{group_id}`         | Get group by ID                                        |
| PUT    | `/groups/{group_id}`         | Update group                                           |
| DELETE | `/groups/{group_id}`         | Delete group                                           |
| GET    | `/items/`                    | List items (paginated, with group displays)            |
| POST   | `/items/`                    | Create item (auto SKU & derived name)                  |
| GET    | `/items/{item_id}`           | Get item by ID                                         |
| PUT    | `/items/{item_id}`           | Update item                                            |
| DELETE | `/items/{item_id}`           | Delete item                                            |
| GET    | `/item-pricelist/`           | List price records (paginated, with item details)      |
| POST   | `/item-pricelist/`           | Create price record                                    |
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
