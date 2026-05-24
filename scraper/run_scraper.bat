@echo off
cd /d D:\eurojackpot-ai
echo Installing dependencies...
pip install --upgrade pip
pip install requests==2.32.3 beautifulsoup4==4.12.3 python-dotenv==1.0.1 "psycopg2-binary>=2.9" "lxml>=5.0" html5lib==1.1
echo.
echo Step 1: Running scraper...
python scraper\advanced_eurojackpot_scraper.py
if %errorlevel% neq 0 (
    echo Scraper failed. Skipping feature rebuild.
    pause
    exit /b 1
)
echo.
echo Step 2: Rebuilding features...
python scripts\rebuild_features.py
if %errorlevel% neq 0 (
    echo Feature rebuild failed.
    pause
    exit /b 1
)
echo.
echo Pipeline complete.
pause
