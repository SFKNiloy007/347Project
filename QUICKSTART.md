# Quick Start Guide - Local Artisan E-Marketplace

## 5-Minute Setup (If PostgreSQL Already Installed)

```powershell
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
.\venv\Scripts\Activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Load database (if first time)
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d artisan_marketplace -f schema.sql

# 5. Start server
python -m uvicorn main:app --reload

# 6. Open browser
# http://127.0.0.1:8000
```

---

## Credentials for Testing

| Role       | Username   | Password      |
| ---------- | ---------- | ------------- |
| 🛍️ Buyer   | `buyer1`   | `password123` |
| 🎨 Artisan | `artisan1` | `password123` |
| 👨‍💼 Admin   | `admin1`   | `password123` |

---

## What Each Role Can Do

### Buyer Dashboard

- Browse available products
- View product details, prices, and stock
- Purchase products (tests race condition prevention)
- View order history

### Artisan Dashboard

- View their own products
- See product stock levels
- Monitor sales

### Admin Dashboard

- View system statistics
- Total users, products, orders
- System monitoring

---

## Key Feature: Race Condition Prevention

The system uses **PostgreSQL row-level locking (FOR UPDATE NOWAIT)** to prevent double-selling:

- When a buyer purchases an item, the product row is locked
- If another buyer tries to purchase simultaneously, they get an error
- This ensures only one purchase succeeds even with concurrent requests

**Test it:**

1. Create a product with stock = 1
2. Open two browser windows logged in as different buyers
3. Both click "Buy Now" simultaneously
4. Only one purchase will succeed!

---

## File Purpose

| File               | Purpose                                         |
| ------------------ | ----------------------------------------------- |
| `main.py`          | FastAPI backend with 15+ REST endpoints         |
| `database.py`      | PostgreSQL connection manager & CRUD operations |
| `schema.sql`       | Database schema (users, products, orders, etc.) |
| `app.html`         | React frontend UI with Tailwind CSS             |
| `requirements.txt` | Python package dependencies                     |
| `INSTALLATION.md`  | Detailed installation guide                     |
| `setup.py`         | Automated setup script                          |

---

## Troubleshooting

### "Connection refused" error

- PostgreSQL not running. Start it:
  - Windows: Services > PostgreSQL > Start
  - Mac: `brew services start postgresql`
  - Linux: `sudo systemctl start postgresql`

### "Invalid password" error

- Update line 42 in `database.py`:
  ```python
  'password': 'YOUR_ACTUAL_PASSWORD'
  ```

### "ModuleNotFoundError: No module named 'fastapi'"

- Virtual environment not activated
- Run: `.\venv\Scripts\Activate`

### Port 8000 already in use

- Use different port:
  ```powershell
  python -m uvicorn main:app --reload --port 8001
  ```

---

## API Endpoints (For Reference)

### Authentication

- `POST /api/login` - Login
- `POST /api/register` - Register new user
- `GET /api/me` - Get current user

### Products

- `GET /api/products` - List all products
- `GET /api/products/{id}` - Get product details
- `POST /api/products` - Create product (Artisan only)

### Orders & Purchases

- `POST /api/purchase` - Make a purchase (CRITICAL: Uses row locking)
- `GET /api/orders` - Get user's orders
- `POST /api/orders/{id}/status` - Update order status

### Admin

- `GET /api/users` - List all users
- `GET /api/transactions` - Financial audit log

---

## API Documentation

Once server is running, visit:

- **http://127.0.0.1:8000/docs** - Interactive API documentation (Swagger UI)
- **http://127.0.0.1:8000/redoc** - Alternative documentation format

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Web Browser                            │
│  app.html (React + Tailwind CSS)                        │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────┐
│         FastAPI Backend (main.py)                        │
│  - JWT Authentication                                    │
│  - Role-based Access Control                             │
│  - Business Logic                                        │
└──────────────────────┬──────────────────────────────────┘
                       │ psycopg2 (Python-PostgreSQL)
┌──────────────────────▼──────────────────────────────────┐
│      PostgreSQL Database (artisan_marketplace)           │
│  - users, products, orders, transactions, audit_logs    │
│  - Row-level locking for concurrency control            │
└──────────────────────────────────────────────────────────┘
```

---

## Key Technologies

| Component  | Technology   | Version |
| ---------- | ------------ | ------- |
| Backend    | FastAPI      | 0.104.1 |
| Frontend   | React        | 18      |
| Database   | PostgreSQL   | 14+     |
| Web Server | Uvicorn      | 0.24.0  |
| Styling    | Tailwind CSS | 3       |
| Security   | JWT + Bcrypt | Latest  |

---

## Next Steps After Setup

1. ✅ Run the application
2. 🧪 Test all three user roles
3. 🛒 Try making a purchase
4. 📊 Check the Admin dashboard
5. 🔒 Review the race condition prevention in `schema.sql` (line: `SELECT ... FOR UPDATE NOWAIT`)

---

## For Faculty/Evaluation

**Key Points to Demonstrate:**

1. **Database Design**: 5 normalized tables with proper relationships
2. **Security**:
   - JWT authentication with bcrypt password hashing
   - Role-based access control
   - Parameterized queries prevent SQL injection
3. **Race Condition Prevention**:
   - PostgreSQL row-level locking with `FOR UPDATE NOWAIT`
   - Prevents double-selling of unique items
   - Can be tested with simultaneous purchases
4. **Full Stack**:
   - Complete REST API with 15+ endpoints
   - Interactive React frontend
   - Responsive design with Tailwind CSS
5. **Production Considerations**:
   - Connection pooling for database efficiency
   - Proper error handling and logging
   - Transaction management

---

Last Updated: December 2024
