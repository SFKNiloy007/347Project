# Local Artisan E-Marketplace - Installation Guide

## System Requirements

- **Windows 10/11** or **macOS/Linux**
- **VS Code** (latest version)
- **Python 3.8+** (preferably 3.10 or higher)
- **PostgreSQL 14+**
- **Git** (optional, for version control)

---

## Step 1: Install PostgreSQL

### Windows:

1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Run the installer
3. During installation:
   - Keep default port `5432`
   - Set a strong password for the `postgres` user (e.g., `6740`)
   - Remember this password - you'll need it later!
4. Complete the installation
5. Verify installation by opening PowerShell and running:
   ```powershell
   & "C:\Program Files\PostgreSQL\16\bin\psql.exe" --version
   ```

### macOS:

```bash
brew install postgresql
brew services start postgresql
```

### Linux (Ubuntu/Debian):

```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

---

## Step 2: Create the Database

1. Open PowerShell (Windows) or Terminal (Mac/Linux)
2. Connect to PostgreSQL:
   ```powershell
   & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres
   ```
3. Create the database:
   ```sql
   CREATE DATABASE artisan_marketplace;
   \q
   ```

---

## Step 3: Install Python Dependencies

1. Open VS Code
2. Open Terminal in VS Code (Ctrl + `)
3. Navigate to the project folder:
   ```powershell
   cd "h:\347 Projectr"
   ```
4. Create a Python virtual environment:
   ```powershell
   python -m venv venv
   ```
5. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate
   ```
6. Install required packages:
   ```powershell
   pip install -r requirements.txt
   ```

Expected output: `Successfully installed fastapi uvicorn psycopg2-binary bcrypt pydantic email-validator`

---

## Step 4: Load the Database Schema

1. In the same terminal, run:
   ```powershell
   & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d artisan_marketplace -f schema.sql
   ```
2. When prompted for password, enter: `6740` (or your chosen PostgreSQL password)
3. You should see output like:
   ```
   DROP TABLE
   CREATE TABLE
   CREATE INDEX
   INSERT 0 3
   ...
   ```

If you get an error about password, update `database.py` with your correct PostgreSQL password:

```python
# Line ~42 in database.py
'password': 'YOUR_POSTGRES_PASSWORD'  # Change this
```

---

## Step 5: Start the Backend Server

1. In VS Code terminal (with venv activated):
   ```powershell
   python -m uvicorn main:app --reload
   ```
2. You should see:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Started server process [XXXX]
   ```

---

## Step 6: Access the Application

1. Open your web browser
2. Go to: **http://127.0.0.1:8000**
3. You should see the login page

### Test Accounts (Pre-configured):

| Role    | Username   | Password      |
| ------- | ---------- | ------------- |
| Buyer   | `buyer1`   | `password123` |
| Artisan | `artisan1` | `password123` |
| Admin   | `admin1`   | `password123` |

---

## Troubleshooting

### Error: "psql: The term 'psql' is not recognized"

**Solution:** Provide the full path to psql:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres
```

### Error: "password authentication failed"

**Solution:**

1. Check your PostgreSQL password is correct
2. Update `database.py` line 42 with the correct password:
   ```python
   'password': 'your_actual_password'
   ```

### Error: "connection to server at "localhost" failed"

**Solution:**

- Windows: Check PostgreSQL is running via Task Manager
- Mac/Linux: Run `brew services start postgresql` or `sudo systemctl start postgresql`

### Error: "No module named 'fastapi'"

**Solution:** Make sure virtual environment is activated:

```powershell
.\venv\Scripts\Activate
```

Then reinstall: `pip install -r requirements.txt`

### Port 8000 already in use

**Solution:** Use a different port:

```powershell
python -m uvicorn main:app --reload --port 8001
```

Then access: http://127.0.0.1:8001

---

## File Structure

```
347 Projectr/
├── main.py                 # FastAPI backend
├── database.py             # Database connection & CRUD
├── schema.sql              # PostgreSQL schema
├── app.html                # Frontend (React)
├── requirements.txt        # Python dependencies
├── INSTALLATION.md         # This file
├── README.md              # Project overview
└── venv/                  # Python virtual environment (created by you)
```

---

## VS Code Extensions (Recommended)

1. **Python** - ms-python.python
2. **Pylance** - ms-python.vscode-pylance
3. **REST Client** - humao.rest-client (for testing APIs)
4. **Thunder Client** or **Postman** (for API testing)

Install them in VS Code: Extensions > Search > Install

---

## Running for Development

Keep this terminal window open and running:

```powershell
python -m uvicorn main:app --reload
```

The `--reload` flag automatically restarts the server when you modify files.

---

## Next Steps

1. ✅ Installation complete!
2. Login with test accounts to explore the marketplace
3. Test the purchase functionality (prevents race conditions with PostgreSQL locking)
4. Review `README.md` for feature overview
5. Check `schema.sql` for database design

---

## Support

If you encounter issues:

1. Check the browser console (F12 > Console tab)
2. Check the terminal output for error messages
3. Ensure all services are running (PostgreSQL, Python server)
4. Verify PostgreSQL password matches `database.py`
