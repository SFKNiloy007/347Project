# Setup Instructions - Local Artisan E-Marketplace

**Complete step-by-step guide to run the application locally**

---

## 📋 Prerequisites

Before starting, ensure you have the following installed on your computer:

### 1. PostgreSQL Database

- **Windows:** Download from https://www.postgresql.org/download/windows/
- **Version:** PostgreSQL 14 or higher
- **During Installation:**
  - Remember the password you set for the `postgres` user
  - Default port: 5432
  - Keep note of the installation directory

### 2. Python

- **Version:** Python 3.9 or higher
- **Download:** https://www.python.org/downloads/
- **Installation Notes:**
  - ✅ Check "Add Python to PATH" during installation
  - Verify installation: Open PowerShell and type `python --version`

### 3. Code Editor (Optional but Recommended)

- **VS Code:** https://code.visualstudio.com/
- Or any text editor you prefer

---

## 🗄️ Step 1: Database Setup

### 1.1 Create Database

Open **pgAdmin 4** (comes with PostgreSQL) or use **psql command line**:

```sql
-- In pgAdmin or psql:
CREATE DATABASE artisan_marketplace;
```

**Using psql (Windows PowerShell):**

```powershell
# Connect to PostgreSQL
psql -U postgres

# Inside psql:
postgres=# CREATE DATABASE artisan_marketplace;
postgres=# \q
```

### 1.2 Run Schema File

Navigate to your project directory and run:

```powershell
# Replace 'postgres' with your PostgreSQL username if different
# You'll be prompted for your PostgreSQL password
psql -U postgres -d artisan_marketplace -f schema.sql
```

**Expected Output:**

```
DROP TABLE
DROP TABLE
CREATE TABLE
CREATE TABLE
...
INSERT 0 3
CREATE FUNCTION
CREATE TRIGGER
CREATE VIEW
```

### 1.3 Verify Database Setup

```powershell
# Connect to database
psql -U postgres -d artisan_marketplace

# Check tables
artisan_marketplace=# \dt

# Should show: users, products, orders, transactions, audit_logs

# Check sample data
artisan_marketplace=# SELECT username, role FROM users;

# Should show: artisan1, buyer1, admin1

# Exit
artisan_marketplace=# \q
```

---

## 🐍 Step 2: Backend Setup

### 2.1 Create Virtual Environment (Recommended)

```powershell
# Navigate to your project directory
cd "h:\347 Projectr"

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Your prompt should now show (venv)
```

**Troubleshooting:** If you get "execution policy" error:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2.2 Install Python Dependencies

```powershell
# Make sure you're in the virtual environment (you should see (venv))
pip install -r requirements.txt
```

**Expected Installation:**

```
Installing collected packages:
  - fastapi
  - uvicorn
  - psycopg2-binary
  - python-jose
  - passlib
  - bcrypt
  - pydantic
  - python-dotenv
  ...
Successfully installed ...
```

**Verify Installation:**

```powershell
pip list
```

### 2.3 Configure Database Connection

The application uses the default connection string:

```
postgresql://postgres:postgres@localhost:5432/artisan_marketplace
```

**If your PostgreSQL password is different:**

**Option A:** Set environment variable (Recommended)

```powershell
# Temporary (for current session only)
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/artisan_marketplace"

# Permanent (add to your PowerShell profile)
[System.Environment]::SetEnvironmentVariable('DATABASE_URL', 'postgresql://postgres:YOUR_PASSWORD@localhost:5432/artisan_marketplace', 'User')
```

**Option B:** Edit `database.py`

```python
# Line 30 in database.py:
self.database_url = database_url or os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:YOUR_PASSWORD@localhost:5432/artisan_marketplace'  # Change here
)
```

### 2.4 Start Backend Server

```powershell
# Make sure you're in the virtual environment
# Your prompt should show (venv)

# Start the server
python -m uvicorn main:app --reload
```

**Expected Output:**

```
INFO:     Will watch for changes in these directories: ['h:\\347 Projectr']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
✓ Database connection pool created successfully
INFO:     Application startup complete.
```

**Verification:**

Open browser and visit:

- **API Root:** http://127.0.0.1:8000/
- **API Documentation:** http://127.0.0.1:8000/docs (Swagger UI)
- **Alternative Docs:** http://127.0.0.1:8000/redoc

You should see JSON response or interactive API documentation.

**Keep this terminal open!** The backend must be running for the frontend to work.

---

## 🌐 Step 3: Frontend Setup

### 3.1 Open Frontend

The frontend is a single HTML file with all dependencies loaded from CDNs.

**Option A: Double-click the file**

- Navigate to `h:\347 Projectr\`
- Double-click `app.html`
- Your default browser should open

**Option B: Open in browser**

- Open any browser (Chrome, Edge, Firefox)
- Press `Ctrl+O` (File → Open)
- Navigate to `h:\347 Projectr\app.html`
- Click Open

**Option C: Using VS Code Live Server (if installed)**

```powershell
# Right-click app.html in VS Code
# Select "Open with Live Server"
```

### 3.2 Verify Frontend Connection

1. **Check Console for Errors:**

   - Press `F12` to open Developer Tools
   - Go to "Console" tab
   - Should not see any red errors
   - If you see CORS errors, ensure backend is running

2. **Test Login:**
   - Username: `artisan1`
   - Password: `password123`
   - Click "Login"

**Success:** You should see the Artisan Dashboard

---

## 🧪 Step 4: Testing the Application

### 4.1 Test User Accounts

The database comes with 3 pre-configured test accounts:

| Username   | Password      | Role    | What You Can Do                 |
| ---------- | ------------- | ------- | ------------------------------- |
| `artisan1` | `password123` | Artisan | Create products, manage orders  |
| `buyer1`   | `password123` | Buyer   | Browse and purchase products    |
| `admin1`   | `password123` | Admin   | View audit logs, financial data |

### 4.2 Test Artisan Features

1. **Login as Artisan:**

   - Username: `artisan1`
   - Password: `password123`

2. **Create a Product:**

   - Click "Create New Product"
   - Fill in details:
     - Product Name: "Handmade Shital Pati"
     - Description: "Traditional cooling mat from Sylhet"
     - Price: 1500
     - Stock: 3
     - Category: "Shital Pati"
   - Click "Create"

3. **View Your Products:**
   - Should see your newly created product
   - Should also see sample products created during setup

### 4.3 Test Buyer Features

1. **Logout** (top right button)

2. **Login as Buyer:**

   - Username: `buyer1`
   - Password: `password123`

3. **Purchase a Product:**

   - Browse available products
   - Click "Buy Now" on any product
   - Enter quantity: `1`
   - Enter shipping address: "123 Dhaka Road, Gulshan, Dhaka"
   - Click "Purchase"

4. **Verify Purchase:**
   - Should see success message with order ID
   - Check "My Orders" section - should see your order

### 4.4 Test Admin Features

1. **Logout**

2. **Login as Admin:**

   - Username: `admin1`
   - Password: `password123`

3. **View Financial Audit:**

   - Should see all transactions
   - Each transaction shows:
     - Total amount
     - Commission fee (5%)
     - Artisan payout (95%)
   - Summary at top shows totals

4. **View All Users:**
   - Should see all registered users
   - Shows username, role, email, join date

### 4.5 Test Bilingual Support

- Click the **🌐 বাংলা** button (top right, near Logout)
- Interface should switch to Bengali
- Click **🌐 English** to switch back

---

## 🔍 Step 5: Testing Race Condition Prevention

**This is the most important test - it demonstrates the core technical achievement!**

### 5.1 Setup

1. **Login as Artisan** and create a product:

   - Name: "Last Item Test"
   - Price: 100
   - **Stock: 1** ← Critical: Only 1 item
   - Create the product

2. **Note the Product ID** from the URL or product card

### 5.2 Test Concurrent Purchase (Manual Method)

1. **Open Two Browser Windows/Tabs:**

   - Window 1: Login as `buyer1`
   - Window 2: Login as a new buyer (register or use another test account)

2. **In Window 1:**

   - Click "Buy Now" on the product with stock = 1
   - Enter shipping address
   - **DON'T CLICK PURCHASE YET**

3. **In Window 2:**

   - Click "Buy Now" on the SAME product
   - Enter shipping address
   - **DON'T CLICK PURCHASE YET**

4. **Now Click "Purchase" in BOTH Windows as Fast as Possible**
   - Try to click at the same time (or within 1 second)

**Expected Result:**

- ✅ One window: "✓ Purchase successful! Order ID: X, Remaining stock: 0"
- ✅ Other window: "✗ Purchase failed: SOLD OUT" or "Product being purchased by another customer"
- ✅ Product stock = 0 (not -1)

**Without proper locking (bug):**

- ❌ Both purchases succeed
- ❌ Stock = -1 (impossible!)

### 5.3 Verify in Database

```powershell
# Connect to database
psql -U postgres -d artisan_marketplace

# Check product stock
SELECT product_id, product_name, stock_quantity FROM products WHERE product_name = 'Last Item Test';

# Should show stock_quantity = 0 (not -1!)

# Check orders
SELECT order_id, buyer_id, product_id, quantity FROM orders WHERE product_id = (SELECT product_id FROM products WHERE product_name = 'Last Item Test');

# Should show only ONE order (not two!)
```

---

## 📊 Step 6: API Testing with Swagger

FastAPI provides an interactive API documentation interface:

1. **Open Swagger UI:**

   - Navigate to: http://127.0.0.1:8000/docs

2. **Test Authentication:**

   - Find "POST /api/login"
   - Click "Try it out"
   - Enter:
     ```json
     {
       "username": "buyer1",
       "password": "password123"
     }
     ```
   - Click "Execute"
   - Copy the `access_token` from the response

3. **Authorize Requests:**

   - Click the green "Authorize" button (top right)
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Click "Authorize"

4. **Test Protected Endpoints:**
   - All requests now include your authentication token
   - Try "GET /api/me" - should return your user data
   - Try "GET /api/buyer/orders" - should return your orders

---

## 🐛 Troubleshooting

### Backend Issues

**Error: "ModuleNotFoundError: No module named 'fastapi'"**

- Solution: Make sure virtual environment is activated
  ```powershell
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

**Error: "psycopg2.OperationalError: could not connect to server"**

- Solution: PostgreSQL is not running
  - Windows: Open Services (Win+R → services.msc)
  - Find "postgresql-x64-14" (or your version)
  - Right-click → Start

**Error: "FATAL: password authentication failed"**

- Solution: Check DATABASE_URL has correct password
  ```powershell
  $env:DATABASE_URL = "postgresql://postgres:YOUR_ACTUAL_PASSWORD@localhost:5432/artisan_marketplace"
  ```

### Frontend Issues

**Error: "Connection error. Please check if the server is running."**

- Solution: Backend is not running
  - Open a terminal
  - Navigate to project directory
  - Run: `python -m uvicorn main:app --reload`

**Error: "CORS policy" in browser console**

- Solution: Make sure:
  - Backend is running on http://127.0.0.1:8000
  - Frontend is accessing http://127.0.0.1:8000/api (not localhost)
  - Try opening frontend in incognito/private mode

**Login works but dashboard is blank:**

- Solution: Check browser console (F12)
  - Look for JavaScript errors
  - Try refreshing the page (Ctrl+F5)

### Database Issues

**Error: "relation 'users' does not exist"**

- Solution: Schema not loaded correctly
  ```powershell
  psql -U postgres -d artisan_marketplace -f schema.sql
  ```

**Products not showing:**

- Solution: Check if sample data exists
  ```powershell
  psql -U postgres -d artisan_marketplace
  artisan_marketplace=# SELECT COUNT(*) FROM products;
  # Should show at least 3
  ```

---

## 🔄 Restarting from Scratch

If you need to completely reset:

### 1. Reset Database

```powershell
# Drop and recreate database
psql -U postgres

postgres=# DROP DATABASE IF EXISTS artisan_marketplace;
postgres=# CREATE DATABASE artisan_marketplace;
postgres=# \q

# Reload schema
psql -U postgres -d artisan_marketplace -f schema.sql
```

### 2. Reset Backend

```powershell
# Stop server (Ctrl+C in terminal)
# Restart server
python -m uvicorn main:app --reload
```

### 3. Reset Frontend

```powershell
# In browser:
# Open Developer Tools (F12)
# Go to "Application" tab
# Find "Local Storage"
# Click on your domain
# Delete the "token" key
# Refresh page (F5)
```

---

## 📁 Project File Structure

```
347 Projectr/
│
├── schema.sql              ← Database schema with tables and sample data
├── database.py             ← Database connection and helper functions
├── main.py                 ← FastAPI backend with all API endpoints
├── app.html                ← React frontend (single-page application)
├── requirements.txt        ← Python dependencies
├── README.md               ← Project documentation (this file)
└── SETUP.md                ← Setup instructions (you are here)
```

---

## 🎓 For Faculty Evaluation

### Quick Demo Script (5 minutes)

1. **Show Database Schema** (1 min)

   - Open pgAdmin → Show tables
   - Explain `products.stock_quantity` critical field

2. **Start Backend** (30 sec)

   - Open terminal → `python -m uvicorn main:app --reload`
   - Show FastAPI docs: http://127.0.0.1:8000/docs

3. **Show Frontend** (1 min)

   - Open `app.html` in browser
   - Login as artisan → Show dashboard
   - Show bilingual support (English/Bangla toggle)

4. **Demonstrate Core Feature** (2 min)

   - Create product with stock = 1
   - Open two browser windows
   - Attempt concurrent purchase
   - Show one succeeds, one fails
   - Verify in database: `SELECT stock_quantity FROM products WHERE ...`

5. **Show Admin Panel** (30 sec)
   - Login as admin
   - Show financial audit with commission tracking

**Total Time:** 5 minutes

### Key Points to Highlight:

1. ✅ **PostgreSQL Row Locking:** `FOR UPDATE NOWAIT` prevents race condition
2. ✅ **ACID Transactions:** All-or-nothing purchase (order + stock update + transaction record)
3. ✅ **Role-Based Security:** JWT + Role checks on every protected endpoint
4. ✅ **Financial Transparency:** 5% commission tracked in `transactions` table
5. ✅ **Audit Trail:** Every action logged in `audit_logs` table

---

## 📞 Support

If you encounter issues not covered here:

1. **Check logs:**

   - Backend: Terminal output where uvicorn is running
   - Frontend: Browser console (F12 → Console tab)
   - Database: Check PostgreSQL logs

2. **Verify basics:**

   - PostgreSQL service is running
   - Virtual environment is activated (you see `(venv)`)
   - Backend is running on port 8000
   - No other application is using port 8000

3. **Test step-by-step:**
   - Can you connect to database? `psql -U postgres`
   - Can you run Python? `python --version`
   - Can you access API docs? http://127.0.0.1:8000/docs

---

**Setup Complete!** You now have a fully functional artisan marketplace with race condition prevention. 🎉

**Next Steps:**

- Read `README.md` for detailed documentation
- Test the concurrent purchase scenario
- Review inline comments in `main.py` and `database.py`
- Explore the auto-generated API docs at http://127.0.0.1:8000/docs
