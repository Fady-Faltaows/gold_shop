# Gold Shop Management System

A comprehensive, production-grade ERP and CRM solution tailored for gold retail businesses. This system integrates real-time gold price calculations, multi-branch inventory tracking, back-office management, and a customer-facing e-commerce storefront.

## Short Description
The Gold Shop Management System is a specialized ERP designed to handle the unique complexities of the jewelry industry, such as karat-based pricing, workmanship fees, and real-time precious metal valuation. It provides tools for both administrators (back-office) and customers (online store).

## Features
- **Real-Time Gold Pricing:** Automated pricing logic based on the latest gold market rates per gram.
- **Back-Office Management:**
    - **Multi-Branch Inventory:** Track stock levels across different physical locations.
    - **Sales & Returns:** Atomic transaction handling with automated stock adjustments.
    - **CRM:** Manage individual and business customers with detailed interaction history.
    - **Supplier Management:** Track purchases, lead times, and supplier performance.
    - **Expense Tracking:** Monitor operational costs like rent, salaries, and utilities.
- **Advanced Reporting:**
    - Financial summaries (Revenue, Gross Profit, Cash Flow).
    - Inventory valuation and low-stock alerts.
    - CSV export capabilities for all primary reports.
- **E-commerce Storefront:**
    - Online product catalog and shopping cart.
    - Customer checkout and order management.
    - "Sell Gold" module: Customers can submit requests to sell gold items to the shop.
- **Mobile PWA Monitor:** A Progress Web App (PWA) dashboard optimized for mobile monitoring of sales and branch performance.
- **Role-Based Access Control (RBAC):** Distinct permissions for Admins and Cashiers.

## Tech Stack
- **Framework:** [Django 6.0.4](https://www.djangoproject.com/)
- **Language:** Python 3.12+
- **Database:** MySQL (Primary), SQLite (Testing/Local)
- **Frontend:** Bootstrap 5, Chart.js (Analytics), Vanilla JavaScript
- **PWA:** django-pwa
- **Imaging:** Pillow (Image processing)

## Project Architecture Overview

The system is structured into two main functional modules (apps):

### 1. `prototype` (Management App)
The core engine of the system.
- **`models.py`:** Contains 12+ entities including `Branch`, `GoldPrice`, `Product`, `Inventory`, `Sale`, `Expense`, and `UserProfile`.
- **`views.py`:** Handles complex business logic, including atomic sales transactions and financial report aggregation.
- **`decorators.py`:** Manages role-based access for Admin and Cashier roles.
- **`urls_mobile.py`:** Dedicated routing for the mobile PWA interface.

### 2. `store` (E-commerce App)
The customer-facing storefront.
- **`models.py`:** Manages `Order`, `OrderItem`, and `OnlinePurchase` (Sell-to-Shop) requests.
- **`context_processors.py`:** Ensures cart counts are globally available across templates.
- **`views.py`:** Manages the shopping cart lifecycle and storefront interactions.

## Installation Guide

### Prerequisites
- Python 3.12 or higher
- MySQL Server 8.0+
- `pip` (Python package manager)

### Step-by-Step Setup
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd gold-shop-project
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file or set the following variables in your environment:
   - `DB_NAME`: `gold_shop_db`
   - `DB_USER`: `gold_admin`
   - `DB_PASSWORD`: `your_secure_password`
   - `DB_HOST`: `localhost`
   - `SECRET_KEY`: Your Django secret key

### Database Setup
1. **Create the MySQL database:**
   ```sql
   CREATE DATABASE gold_shop_db CHARACTER SET utf8mb4;
   ```

2. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Create a superuser (Admin):**
   ```bash
   python manage.py createsuperuser
   ```

### Running Server
```bash
python manage.py runserver
```
The system will be available at `http://127.0.0.1:8000`.

## Usage Guide

### 1. Setting Gold Prices
Administrators must update the gold price regularly. Navigate to the **Gold Price** section in the dashboard and add the current price per gram. All subsequent sales calculations will use this "latest" price.

### 2. Managing Inventory
- Add **Branches** first.
- Create **Products** with specific Karat (18K, 21K, 24K) and weight.
- Use the **Purchases** module to add stock to specific branches.

### 3. Processing a Sale
- Go to **Sales > New Sale**.
- Select items (optionally use a barcode scanner).
- The system automatically calculates the price based on: `(Gold Price * Karat Purity * Weight) + Workmanship Fee`.
- Confirming the sale automatically deducts stock from the current branch.

### 4. Online Store & Sell Gold
- Customers can visit the `/store/` path to browse and buy.
- The "Sell Gold" feature allows customers to upload photos and descriptions of gold they wish to sell, which admins can review in the back-office.

## API Endpoints
While primarily a Monolithic template-based app, the following key functional endpoints exist:
- `GET /reports/sales/export.csv`: Export sales data.
- `GET /reports/financial/export.csv`: Export financial summaries.
- `GET /mobile/api/stats/`: JSON endpoint for PWA dashboard updates.

## Testing
To run the automated test suite (uses a separate SQLite database):
```bash
python manage.py test
```

## Common Issues & Fixes
- **Database Connection Error:** Ensure MySQL is running and the `gold_admin` user has full privileges on `gold_shop_db`.
- **Missing Images:** Ensure the `media/` directory is writable by the web server.
- **PWA Not Loading:** Ensure you are accessing the site over `HTTPS` or `localhost` as service workers require a secure context.

## Security Notes
- **RBAC:** Cashiers are strictly limited to their assigned branch data.
- **Session Security:** `CSRF` protection is enabled on all forms.
- **Data Integrity:** `SaleItem` records snapshot the price at the time of sale to ensure historical accuracy even if gold prices or product data change later.

## Future Improvements
- **Advanced Barcode Support:** Full integration for mobile camera scanning.
- **Automated Pricing API:** Integration with live global gold price APIs.
- **Multi-Currency Support:** Ability to handle transactions in different currencies with live exchange rates.

## Contributing Guide
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/NewFeature`).
3. Commit your changes (`git commit -m 'Add NewFeature'`).
4. Push to the branch (`git push origin feature/NewFeature`).
5. Open a Pull Request.

## License
*Placeholder: All rights reserved.* (Replace with your specific license, e.g., MIT, GPL).
