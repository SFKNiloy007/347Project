#!/usr/bin/env python3
"""
Quick Setup Script for Local Artisan E-Marketplace
Automates Python environment and database setup
"""

import os
import sys
import subprocess
import platform


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def run_command(cmd, description):
    """Run a command and show status"""
    print(f"▶ {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} - SUCCESS")
            return True
        else:
            print(f"✗ {description} - FAILED")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"✗ {description} - ERROR: {str(e)[:100]}")
        return False


def main():
    print_header("LOCAL ARTISAN E-MARKETPLACE SETUP")

    # Step 1: Check Python
    print("Step 1: Checking Python Installation")
    if sys.version_info < (3, 8):
        print("✗ Python 3.8+ required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

    # Step 2: Create virtual environment
    print_header("Step 2: Setting up Python Environment")
    if not os.path.exists("venv"):
        if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
            sys.exit(1)
    else:
        print("✓ Virtual environment already exists")

    # Step 3: Install dependencies
    print_header("Step 3: Installing Dependencies")
    if os.path.exists("requirements.txt"):
        pip_cmd = f"venv\\Scripts\\pip" if platform.system() == "Windows" else "venv/bin/pip"
        if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing packages"):
            print("⚠ Warning: Package installation had issues")
    else:
        print("✗ requirements.txt not found")

    # Step 4: Database setup instructions
    print_header("Step 4: Database Setup")
    print("""
PostgreSQL Configuration:
1. Have you installed PostgreSQL 14+? 
   - Windows: https://www.postgresql.org/download/windows/
   - Mac: brew install postgresql
   - Linux: sudo apt-get install postgresql

2. Create the database by running in PowerShell/Terminal:
   
   Windows:
   & "C:\\Program Files\\PostgreSQL\\16\\bin\\psql.exe" -U postgres
   CREATE DATABASE artisan_marketplace;
   \\q
   
   Mac/Linux:
   psql -U postgres
   CREATE DATABASE artisan_marketplace;
   \\q

3. Load the schema:
   Windows:
   & "C:\\Program Files\\PostgreSQL\\16\\bin\\psql.exe" -U postgres -d artisan_marketplace -f schema.sql
   
   Mac/Linux:
   psql -U postgres -d artisan_marketplace -f schema.sql
""")

    # Step 5: Configuration check
    print_header("Step 5: Configuration")
    print("""
Before running the server:

1. Update database.py if needed:
   - Open database.py
   - Find line ~42: 'password': '6740'
   - Change '6740' to your PostgreSQL password

2. Verify schema.sql was loaded:
   Windows: & "C:\\Program Files\\PostgreSQL\\16\\bin\\psql.exe" -U postgres -d artisan_marketplace -c "SELECT COUNT(*) FROM users;"
   Mac/Linux: psql -U postgres -d artisan_marketplace -c "SELECT COUNT(*) FROM users;"
   
   You should see: count = 3 (artisan1, buyer1, admin1)
""")

    # Step 6: Startup instructions
    print_header("Step 6: Ready to Start!")
    print("""
To start the application:

1. Open Terminal in VS Code (Ctrl + `)
2. Activate virtual environment:
   - Windows: .\\venv\\Scripts\\Activate
   - Mac/Linux: source venv/bin/activate
   
3. Start the server:
   python -m uvicorn main:app --reload
   
4. Open browser to: http://127.0.0.1:8000

5. Login with:
   Username: buyer1
   Password: password123
""")

    print_header("Setup Complete!")
    print("""
Next steps:
- Ensure PostgreSQL is running
- Load the database schema (see Step 4)
- Run 'python -m uvicorn main:app --reload'
- Open http://127.0.0.1:8000 in your browser

For detailed instructions, see INSTALLATION.md
""")


if __name__ == "__main__":
    main()
