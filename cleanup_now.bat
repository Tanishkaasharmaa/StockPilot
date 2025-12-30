@echo off
move ACCURACY_REPORT.md docs\
move ACCURACY_SUMMARY.md docs\
move EVENT_MONITOR.md docs\
move REACTIVE_INTELLIGENCE.md docs\
move TESTING_GUIDE.md docs\
move .env config\
move Data\* data\
del app.py agent.py event_monitor.py reactive_intelligence.py database.py embeddings.py ingest_docs.py simple_store.py cleanup.bat reorganize.bat
rmdir Data /S /Q
echo Cleanup complete.
