@echo off
REM =============================================================================
REM S-ACM (Smart Academic Content Management) - Project Runner
REM =============================================================================
REM This script creates a virtual environment, installs dependencies,
REM runs database migrations, sets up initial data, and starts the server.
REM =============================================================================

echo ============================================================
echo   S-ACM - Smart Academic Content Management System
echo   Automated Setup and Run Script
echo ============================================================
echo.

REM --- Step 1: Check Python availability ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found.

REM --- Step 2: Create virtual environment ---
if not exist "venv" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)

REM --- Step 3: Activate virtual environment ---
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo [OK] Virtual environment activated.

REM --- Step 4: Upgrade pip ---
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip --quiet

REM --- Step 5: Install requirements ---
echo [SETUP] Installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

REM --- Step 6: Check .env file ---
if not exist ".env" (
    if exist ".env.example" (
        echo [SETUP] Creating .env from .env.example...
        copy .env.example .env >nul
        echo [WARNING] Please edit .env with your actual configuration!
    ) else (
        echo [WARNING] No .env file found. Using default settings.
    )
) else (
    echo [OK] .env file found.
)

REM --- Step 7: Collect static files ---
echo [SETUP] Collecting static files...
python manage.py collectstatic --noinput --quiet 2>nul
echo [OK] Static files collected.

REM --- Step 8: Run database migrations ---
echo [SETUP] Running database migrations...
python manage.py migrate --run-syncdb
if %errorlevel% neq 0 (
    echo [ERROR] Migration failed. Check database settings in .env
    pause
    exit /b 1
)
echo [OK] Database migrations complete.

REM --- Step 9: Setup initial data ---
echo [SETUP] Setting up initial data (roles, permissions, levels)...
python manage.py setup_initial_data
if %errorlevel% neq 0 (
    echo [WARNING] Initial data setup had issues. Continuing...
)
echo [OK] Initial data ready.

REM --- Step 10: Run tests (optional) ---
echo.
set /p RUN_TESTS="Run tests before starting? (y/N): "
if /i "%RUN_TESTS%"=="y" (
    echo [TEST] Running test suite...
    python manage.py test tests.test_comprehensive -v1
    if %errorlevel% neq 0 (
        echo [WARNING] Some tests failed. Check the output above.
    ) else (
        echo [OK] All tests passed!
    )
)

REM --- Step 11: Start the server ---
echo.
echo ============================================================
echo   Starting S-ACM Development Server
echo   URL: http://127.0.0.1:8000
echo   Admin: http://127.0.0.1:8000/scam-admin/
echo   Default Admin: academic_id=admin, password=admin123
echo ============================================================
echo   Press Ctrl+C to stop the server.
echo ============================================================
echo.

python manage.py runserver 0.0.0.0:8000

pause
