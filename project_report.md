# Project Architecture & State Report

## 1. Project Overview & Tech Stack
- **Core Stack:** Python 3.x, Django 6.0.4
- **Database:** MySQL (configured as primary in `settings.py`), SQLite (used for testing and local development)
- **Key Dependencies:** 
  - `Django==6.0.4`: Web framework
  - `pillow==12.2.0`: Image processing (for product/category images)
  - `psycopg2-binary`: PostgreSQL adapter (present in requirements)
  - `mysqlclient`: Implied by MySQL configuration in settings
- **Project Purpose:** A comprehensive Gold Shop Management System (ERP/CRM) designed to track inventory, manage sales transactions with real-time gold price calculations, handle customer/supplier relationships, and generate financial reports.

## 2. Directory & File Structure
```text
gold_shop/
├── gold_shop/                  # Project-level configuration
│   ├── settings.py             # Core settings (DB, Auth, Apps, Media)
│   ├── urls.py                 # Root URL routing (includes prototype.urls)
│   └── wsgi.py / asgi.py       # Deployment interfaces
├── prototype/                  # Primary application module
│   ├── models.py               # 12+ Core models (Sales, Products, Inventory, etc.)
│   ├── views.py                # Business logic (900+ lines including reports & exports)
│   ├── urls.py                 # Endpoint definitions (CRM, Sales, Inventory, Reports)
│   ├── forms.py                # Django ModelForms with Bootstrap styling
│   ├── decorators.py           # Role-based access control (Admin/Cashier)
│   └── templates/              # HTML templates (Prototype/Auth/Reports)
├── media/                      # User-uploaded content (Product images)
├── static/                     # CSS/JS assets
├── manage.py                   # Django CLI tool
└── requirements.txt            # Python dependency manifest
```

## 3. Data Models & Core Logic
- **Database Schema / Models:**
  - `Branch`: Manages physical shop locations.
  - `GoldPrice`: Stores price history; logic uses the `latest()` price for transactions.
  - `Product`: Stores karat (18K, 21K, 24K), weight, and workmanship fees.
  - `Inventory`: Tracks stock levels per Branch using `unique_together` on product/branch.
  - `Sale` & `SaleItem`: Atomic transactions; snapshots gold price at time of sale and calculates profit based on cost vs. selling price.
  - `Customer` & `Supplier`: CRM entities with unique code generation (e.g., `SUP-XXXX`).
  - `Expense`: Categories like Rent, Salary, Utilities.
  - `UserProfile`: Extends Django User with `role` (Admin/Cashier) and `branch` assignment.

- **Key Components / Endpoints:**
  - `sale_create`: Complex view handling multi-item transactions, stock validation, and automated inventory deduction.
  - `financial_report`: Aggregates revenue, gross profit, and cash flow across date ranges and branches.
  - `report_inventory`: Identifies low-stock items based on per-product thresholds.

## 4. Configuration & Environment State
- **Authentication:** Role-based access control (RBAC). Admins see global data; Cashiers are restricted to their assigned branch data.
- **Database State:** Configured for MySQL (`gold_shop_db`). `db.sqlite3` exists locally for quick prototyping.
- **Internationalization:** Set to `en-us` with `Africa/Cairo` timezone.
- **Static/Media:** Fully configured with `MEDIA_ROOT` for product image uploads.

## 5. Current Implementation Stage
- **Completed Features:** 
    - Full Sales/Purchase lifecycle with inventory auto-updates.
    - Automated gold price snapshotting per transaction.
    - Financial reporting with CSV export capabilities.
    - CRM and Supplier management modules.
    - Role-based dashboard stats (Profit, Revenue, Low Stock).
- **Pending / Empty Boilerplates:**
    - `CustomerInteraction` model is defined but lacks a full UI/View implementation.
    - Advanced analytics (Chart.js) were recently integrated but may require further visualization refinements.
    - Barcode scanner integration is in the implementation phase for product lookups in sales/inventory.
