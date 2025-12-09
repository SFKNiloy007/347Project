# Setup Checklist for Another Laptop

Complete these steps in order to get the application running.

## Pre-Installation (5 minutes)

- [ ] Install PostgreSQL 14+ from https://www.postgresql.org/download/
  - Remember the password you set for the `postgres` user
  - Note: If password is something like `Niloy@1`, use it in Step 3c
- [ ] Install Python 3.10+ from https://www.python.org/downloads/
  - Check "Add Python to PATH" during installation
- [ ] Install VS Code from https://code.visualstudio.com/

---

## Installation Steps

### Step 1: Open the Project Folder

- [ ] Open VS Code
- [ ] File > Open Folder > Select the `347 Projectr` folder
- [ ] Open Terminal in VS Code (Ctrl + `)

### Step 2: Create Python Virtual Environment

```powershell
python -m venv venv
```

- [ ] Wait for the venv folder to be created

### Step 3: Activate Virtual Environment

```powershell
.\venv\Scripts\Activate
```

- [ ] You should see `(venv)` in your terminal prompt

### Step 4: Install Python Packages

```powershell
pip install -r requirements.txt
```

- [ ] Wait until you see "Successfully installed..."

### Step 5a: Create PostgreSQL Database (First Time Only)

**Windows:**

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres
```

**Mac:**

```bash
psql -U postgres
```

Then in the psql prompt, type:

```sql
CREATE DATABASE artisan_marketplace;
\q
```

- [ ] Successfully created database

### Step 5b: Load Database Schema

**Windows:**

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d artisan_marketplace -f schema.sql
```

**Mac/Linux:**

```bash
psql -U postgres -d artisan_marketplace -f schema.sql
```

When prompted: Enter your PostgreSQL password

Expected output:

```
DROP TABLE
CREATE TABLE
CREATE INDEX
INSERT 0 3
CREATE FUNCTION
CREATE TRIGGER
CREATE VIEW
```

- [ ] Schema loaded successfully

### Step 5c: Update Database Password (If Needed)

If the schema loaded with an error about password, you need to update `database.py`:

1. Open `database.py` in VS Code
2. Find line around 42:
   ```python
   'password': '6740'
   ```
3. Replace `'6740'` with your actual PostgreSQL password
4. Save the file

- [ ] Database password configured

### Step 6: Start the Backend Server

With virtual environment still activated:

```powershell
python -m uvicorn main:app --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started server process [12345]
INFO:     Application startup complete.
```

- [ ] Server running successfully (Leave this terminal open!)

### Step 7: Access the Application

1. Open your web browser
2. Go to: **http://127.0.0.1:8000**
3. You should see the login page with a beautiful purple gradient background

- [ ] Login page displaying

### Step 8: Test Login

Try logging in with one of the test accounts:

**Buyer Account:**

- Username: `buyer1`
- Password: `password123`

Or:

**Artisan Account:**

- Username: `artisan1`
- Password: `password123`

Or:

**Admin Account:**

- Username: `admin1`
- Password: `password123`

- [ ] Successfully logged in
- [ ] Dashboard displaying (Buyer/Artisan/Admin dashboard)

---

## Verify Installation

After logging in, check these features work:

### Buyer Features

- [ ] Can see product list on Buyer Dashboard
- [ ] Product shows name, price, stock quantity
- [ ] Can click "Buy Now" button
- [ ] After purchase, gets success message
- [ ] Can click "Buy Now" again (stock decreases)

### Artisan Features

- [ ] Can see their products (created by them)
- [ ] Products show stock levels
- [ ] Can see prices

### Admin Features

- [ ] Dashboard shows statistics
- [ ] Shows number of users, products, orders
- [ ] Stats update after purchases

---

## Troubleshooting

### Issue: "psql: command not found"

**Solution:** Use full path:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres
```

### Issue: "password authentication failed"

**Solution:**

- You entered the wrong PostgreSQL password
- Edit `database.py` line 42 and change the password
- Save the file
- The server should auto-reload

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**

- Virtual environment not activated
- Run: `.\venv\Scripts\Activate`
- You should see `(venv)` in the prompt

### Issue: "port 8000 already in use"

**Solution:**

```powershell
python -m uvicorn main:app --reload --port 8001
```

Then access: http://127.0.0.1:8001

### Issue: "connection to server at localhost failed"

**Solution:**

- PostgreSQL is not running
- Windows: Open Services and start PostgreSQL
- Mac: Run `brew services start postgresql`
- Linux: Run `sudo systemctl start postgresql`

### Issue: "TypeError: products.filter is not a function"

**Solution:** Hard refresh the page (Ctrl + Shift + R)

---

## File Overview

| File               | What it does                         |
| ------------------ | ------------------------------------ |
| `main.py`          | Backend REST API server              |
| `database.py`      | Database connection and operations   |
| `schema.sql`       | Database schema - run this once      |
| `app.html`         | Frontend UI - loaded automatically   |
| `requirements.txt` | Python package list - installed once |
| `venv/`            | Virtual environment - created by you |

---

## Once Everything Works

### To stop the server:

Press `Ctrl + C` in the terminal

### To start it again:

```powershell
.\venv\Scripts\Activate
python -m uvicorn main:app --reload
```

### To keep it running permanently:

Remove `--reload` flag:

```powershell
python -m uvicorn main:app
```

---

## Getting Help

1. Check the error message in the terminal
2. Search for the error in `INSTALLATION.md`
3. Check browser console: Press F12 > Console tab
4. Verify PostgreSQL is running
5. Verify all services are started

---

## Time Estimate

- First time setup: **15-20 minutes**
- Subsequent startups: **30 seconds** (activate venv + start server)

---

## Success Indicators

✅ Virtual environment created with `venv` folder
✅ All Python packages installed (no errors)
✅ Database created and schema loaded
✅ Server running on http://127.0.0.1:8000
✅ Login page displays
✅ Can login with test accounts
✅ Dashboard appears after login
✅ Products display with prices and stock
✅ Can click "Buy Now" button

---

## Next: Explore Features

After successful login, try:

1. **As Buyer:**

   - Browse products
   - Click "Buy Now"
   - Check if stock decreases

2. **As Artisan:**

   - See your products
   - View stock levels

3. **As Admin:**

   - Check dashboard statistics
   - Verify counts update after purchases

4. **Race Condition Test:**
   - Login as buyer1 in one browser window
   - Login as buyer2 (create new account) in another window
   - Find product with stock=1
   - Both click "Buy Now" simultaneously
   - Only one purchase succeeds! (This is the key feature)

---

**Ready to setup? Start with Step 1 above!**

Questions? Check INSTALLATION.md and QUICKSTART.md for detailed information.
