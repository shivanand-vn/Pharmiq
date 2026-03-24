# PharmIQ — Entity Relationship Diagram

## ER Diagram

```mermaid
erDiagram
    DISTRIBUTORS {
        INT distributor_id PK
        VARCHAR name
        VARCHAR mobile_no
        VARCHAR email
        TEXT address
        VARCHAR gst_no
        VARCHAR drug_license_no
        VARCHAR logo_path
        VARCHAR bank_name
        VARCHAR bank_account_no
        VARCHAR bank_ifsc
        VARCHAR bank_branch
        VARCHAR bank_upi
        VARCHAR signatory_name
        VARCHAR signatory_img_path
        ENUM status
        TIMESTAMP created_at
    }

    LICENSES {
        INT license_id PK
        INT distributor_id FK
        DATE start_date
        DATE expiry_date
        DECIMAL amount_paid
        ENUM status
    }

    USERS {
        INT user_id PK
        INT distributor_id FK
        VARCHAR username
        VARCHAR password
        VARCHAR temp_password
        TINYINT is_first_login
        ENUM status
    }

    ROLES {
        INT role_id PK
        VARCHAR role_name
    }

    USER_ROLES {
        INT user_id FK
        INT role_id FK
    }

    CUSTOMERS {
        VARCHAR license_no PK
        INT distributor_id FK
        VARCHAR shop_name
        VARCHAR license_holder_name
        VARCHAR mobile_no
        VARCHAR gst_no
        VARCHAR email
        TEXT address
        ENUM status
        TIMESTAMP created_at
    }

    SUPPLIERS {
        INT supplier_id PK
        INT distributor_id FK
        VARCHAR name
        VARCHAR mobile_no
        VARCHAR gst_no
    }

    MEDICINES {
        INT medicine_id PK
        VARCHAR name
        VARCHAR unit
        DECIMAL gst_percent
    }

    BATCHES {
        INT batch_id PK
        INT medicine_id FK
        INT supplier_id FK
        INT distributor_id FK
        VARCHAR batch_no
        DATE expiry_date
        INT quantity
        DECIMAL purchase_price
        DECIMAL mrp
    }

    PURCHASES {
        INT purchase_id PK
        INT supplier_id FK
        INT distributor_id FK
        INT user_id FK
        DATE date
        DECIMAL total_amount
    }

    PURCHASE_ITEMS {
        INT purchase_item_id PK
        INT purchase_id FK
        INT batch_id FK
        INT quantity
        DECIMAL price
    }

    SALES {
        INT sale_id PK
        INT distributor_id FK
        INT user_id FK
        VARCHAR license_no FK
        DATE date
        DECIMAL total_amount
        DECIMAL gst_amount
        DECIMAL discount
        DECIMAL grand_total
    }

    SALE_ITEMS {
        INT sale_item_id PK
        INT sale_id FK
        INT batch_id FK
        INT quantity
        DECIMAL price
        DECIMAL gst_percent
        DECIMAL gst_value
    }

    INVOICES {
        INT invoice_id PK
        VARCHAR invoice_no
        INT distributor_id FK
        INT user_id FK
        VARCHAR customer_license_no FK
        DATE invoice_date
        VARCHAR order_no
        VARCHAR lr_no
        VARCHAR transport
        ENUM payment_type
        DECIMAL subtotal
        DECIMAL discount_amount
        DECIMAL sgst
        DECIMAL cgst
        DECIMAL total_gst
        DECIMAL grand_total
        VARCHAR amount_in_words
        TIMESTAMP created_at
    }

    INVOICE_ITEMS {
        INT item_id PK
        INT invoice_id FK
        INT batch_id FK
        VARCHAR product_name
        VARCHAR batch_no
        DATE expiry_date
        INT qty
        DECIMAL mrp
        DECIMAL rate
        DECIMAL discount_percent
        DECIMAL gst_percent
        DECIMAL amount
    }

    %% ── Relationships ──

    DISTRIBUTORS ||--o{ LICENSES : "has"
    DISTRIBUTORS ||--o{ USERS : "has"
    DISTRIBUTORS ||--o{ CUSTOMERS : "manages"
    DISTRIBUTORS ||--o{ SUPPLIERS : "manages"
    DISTRIBUTORS ||--o{ BATCHES : "stocks"
    DISTRIBUTORS ||--o{ PURCHASES : "makes"
    DISTRIBUTORS ||--o{ SALES : "records"
    DISTRIBUTORS ||--o{ INVOICES : "generates"

    USERS }o--o{ ROLES : "USER_ROLES"

    SUPPLIERS ||--o{ BATCHES : "supplies"
    SUPPLIERS ||--o{ PURCHASES : "fulfills"
    MEDICINES ||--o{ BATCHES : "has"

    PURCHASES ||--o{ PURCHASE_ITEMS : "contains"
    BATCHES ||--o{ PURCHASE_ITEMS : "referenced in"

    CUSTOMERS ||--o{ SALES : "buys"
    USERS ||--o{ SALES : "creates"
    SALES ||--o{ SALE_ITEMS : "contains"
    BATCHES ||--o{ SALE_ITEMS : "referenced in"

    CUSTOMERS ||--o{ INVOICES : "billed to"
    USERS ||--o{ INVOICES : "created by"
    USERS ||--o{ PURCHASES : "created by"
    INVOICES ||--o{ INVOICE_ITEMS : "contains"
    BATCHES ||--o{ INVOICE_ITEMS : "referenced in"
```

---

## Relationship Summary

| Relationship | Type | Description |
|---|---|---|
| Distributors → Users | 1:M | Each distributor has multiple users |
| Distributors → Licenses | 1:M | Subscription licenses per distributor |
| Distributors → Customers | 1:M | Each distributor manages their own customers |
| Distributors → Suppliers | 1:M | Suppliers are scoped per distributor |
| Users ↔ Roles | M:N | Via `user_roles` junction table (Admin, Biller, Accountant) |
| Medicines → Batches | 1:M | One medicine can have many batches |
| Suppliers → Batches | 1:M | Each batch sourced from one supplier |
| Distributors → Batches | 1:M | Stock is isolated per distributor |
| Purchases → Purchase Items | 1:M | Each purchase has line items |
| Sales → Sale Items | 1:M | Each sale has line items |
| Invoices → Invoice Items | 1:M | Each invoice has product line items |
| Customers → Sales/Invoices | 1:M | Customer appears on sales and invoices |

## System Flow

```mermaid
flowchart TD
    A["Developer"] -->|Creates| B["Distributor"]
    B -->|Assigns| C["License"]
    B -->|Creates| D["Users"]
    D -->|Assigned| E["Roles (Admin/Biller/Accountant)"]
    D -->|Login + License Check| F["System Access"]
    F --> G["Manage Customers"]
    F --> H["Manage Suppliers"]
    F --> I["Purchase Stock"]
    F --> J["Create Sales"]
    F --> K["Generate Invoices"]
    K -->|Creates| L["Invoice PDF"]
    I -->|Updates| M["Batches (Stock)"]
    J -->|Reduces| M
    K -->|Reduces| M
```
