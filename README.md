# ERP Backend — Item, HR, Sales, & Sales Order Modules

Asynchronous FastAPI backend for the ERP system's **Item Master** (`inventory` schema), **HR & Sales** modules (`hr` and `sales` schemas), **Sales Order** module (`sales` schema), and supporting lookup tables (`system` schema).

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
│   │   ├── customer.py          # sales.customer
│   │   └── sales_order.py       # sales.order_header & sales.order_detail
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── envelope.py          # Envelope[T], PaginationModel, LinksModel, ErrorModel, MetaModel
│   │   ├── group.py             # GroupCreate / GroupUpdate / GroupRead
│   │   ├── item.py              # ItemCreate / ItemUpdate / ItemRead (+ group display fields)
│   │   ├── item_pricelist.py    # ItemPriceListCreate / Update / Read
│   │   ├── employee.py          # EmployeeCreate / Update / Read
│   │   ├── sales_person.py      # SalesPersonCreate / Update / Read
│   │   ├── customer.py          # CustomerCreate / Update / Read
│   │   └── sales_order.py       # OrderHeaderCreate / Update / Read & OrderDetail schemas
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── base.py              # Generic CRUD base (incl. page/offset pagination & .unique())
│   │   ├── group.py             # group_crud instance + get_group_display & populate_group_displays
│   │   ├── item.py              # CRUDItem: SKU generation, item_name derivation, group lookup population
│   │   ├── item_pricelist.py    # item_pricelist_crud instance
│   │   ├── employee.py          # employee_crud instance + group display population
│   │   ├── sales_person.py      # sales_person_crud instance + group display population
│   │   ├── customer.py          # customer_crud instance + group display population
│   │   └── sales_order.py       # sales_order_crud instance (doc_no generation, doc_duedate calculation)
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
│       ├── customer.py          # /customers
│       └── sales_order.py       # /sales-orders
├── alembic/
│   ├── env.py                   # Loads DATABASE_URL_SYNC dynamically from settings
│   └── versions/
│       ├── 7c67a18f645e_create_inventory_and_system_schemas.py
│       ├── 5c9ca3d9408d_create_group_item_item_pricelist_tables.py
│       ├── 63b865b5ada5_rename_id_to_pricelist_id_in_item_.py
│       ├── ed7260bbaf85_create_hr_and_sales_schemas_and_tables.py
│       ├── 2781c4f12188_add_customer_top_to_sales_customer.py
│       ├── 98a7b6c5d4e3_rename_group_value_to_group_display_and_add_integer_value.py
│       └── 39a8b7c6d5e4_create_sales_order_tables.py
├── alembic.ini
├── requirements.txt
├── .env / .env.example
├── sales order schema.md        # Sales Order module specs
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
python scripts/seed_groups.py # populates system lookup groups (Item Master, Employee, Customer, Sales Person, Customer TOP with day offsets)
alembic downgrade -1          # rollback one step
```

- Migration 1 (`7c67a18f645e`): creates `inventory` and `system` schemas.
- Migration 2 (`5c9ca3d9408d`): creates `system.group`, `inventory.item`, and `inventory.item_pricelist`.
- Migration 3 (`63b865b5ada5`): renames `id` to `pricelist_id` in `inventory.item_pricelist`.
- Migration 4 (`ed7260bbaf85`): creates `hr` and `sales` schemas and tables (`hr.employee`, `sales.sales_person`, `sales.customer`).
- Migration 5 (`2781c4f12188`): adds `customer_top` and composite FK to `sales.customer`.
- Migration 6 (`98a7b6c5d4e3`): renames `system.group.group_value` to `group_display` and adds integer `group_value` for day-offset calculations.
- Migration 7 (`39a8b7c6d5e4`): creates `sales.order_header` and `sales.order_detail`.
- **Seeder Script (`scripts/seed_groups.py`)**: scans all group mappings across application modules and idempotently populates `system.group` with display text and integer day-offset values.

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
| group_id        | SERIAL       | Primary key                                                |
| group_noid      | SMALLINT     | Not null, unique within a `group_name`                     |
| group_name      | VARCHAR(50)  | Not null, lookup category                                  |
| group_display   | VARCHAR(100) | Not null, display text (e.g. `NET 15`, `ACTIVE`, `STAFF`)  |
| group_value     | INTEGER      | Nullable, integer value / day-offset (e.g. `15` for NET 15)|

### `inventory.item` & `inventory.item_pricelist`
- Item Master and Pricelist tables as documented previously.

### HR, Sales, & Sales Order Tables (`hr.employee`, `sales.sales_person`, `sales.customer`, `sales.order_header`, `sales.order_detail`)
- **`hr.employee`**: `employee_id`, `employee_no`, `employee_name`, `position`, `department`, `join_date`, `status`.
- **`sales.sales_person`**: `sales_person_id`, `employee_id`, `sales_person_no`, `sales_area`, `sales_level`, `status`.
- **`sales.customer`**: `customer_id`, `customer_no`, `customer_name`, `customer_type`, `customer_top`, `sales_person_id`, `address`, `city_region`, `phone`, `status`.
- **`sales.order_header`**: `doc_id`, `doc_no` (`SOYYMM0001`), `doc_date`, `doc_duedate` (auto-calculated from `doc_terms` day-offset), `doc_terms` (FK to `CUSTOMER TOP`), `cust_id`, `dropship_id`, `sales_id`.
- **`sales.order_detail`**: `trans_id`, `doc_id`, `trans_idx` (sequential per order), `item_id`, `trans_qty` (> 0), `trans_price`, `trans_total` (`qty * price`), unique on `(doc_id, item_id)`.

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
