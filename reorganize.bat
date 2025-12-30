@echo off
echo Reorganizing project structure...
echo.

REM Move Python source files
echo Moving source files...
move app.py src\ 2>nul
move agent.py src\core\ 2>nul
move event_monitor.py src\core\ 2>nul
move reactive_intelligence.py src\core\ 2>nul
move database.py src\database\ 2>nul
move embeddings.py src\database\ 2>nul
move ingest_docs.py src\utils\ 2>nul
move simple_store.py src\utils\ 2>nul

REM Move data files
echo Moving data files...
move hugo.db data\ 2>nul
move simple_docs.json data\ 2>nul
move event_log.json data\ 2>nul
move Data data\Data 2>nul
move chroma_db data\chroma_db 2>nul

REM Move documentation
echo Moving documentation...
move ACCURACY_REPORT.md docs\ 2>nul
move ACCURACY_SUMMARY.md docs\ 2>nul
move EVENT_MONITOR.md docs\ 2>nul
move REACTIVE_INTELLIGENCE.md docs\ 2>nul
move TESTING_GUIDE.md docs\ 2>nul

REM Move configuration
echo Moving configuration...
move .env config\ 2>nul

REM Create __init__.py files for Python packages
echo Creating __init__.py files...
type nul > src\__init__.py
type nul > src\core\__init__.py
type nul > src\database\__init__.py
type nul > src\utils\__init__.py

echo.
echo Folder reorganization complete!
echo.
pause
