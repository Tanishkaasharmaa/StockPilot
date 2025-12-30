@echo off
echo Starting cleanup of debug and test files...
echo.

REM Debug scripts
del /Q check_parts.py 2>nul
del /Q check_syntax.py 2>nul
del /Q debug_syntax.py 2>nul
del /Q debug_events.py 2>nul
del /Q debug_gemini.py 2>nul
del /Q debug_headlights.py 2>nul
del /Q debug_search.py 2>nul
del /Q debug_surge.py 2>nul
del /Q debug_tool_call.py 2>nul

REM Test files
del /Q test.py 2>nul
del /Q test_agent_accuracy.py 2>nul
del /Q test_agent_output.py 2>nul
del /Q test_assistant.py 2>nul
del /Q test_assistant_loops.py 2>nul
del /Q test_email_outbox.py 2>nul
del /Q test_event_monitor.py 2>nul
del /Q test_memory_fix.py 2>nul
del /Q test_search.py 2>nul
del /Q test_simulation.py 2>nul
del /Q test_tool_directly.py 2>nul
del /Q test_tool_fixes.py 2>nul
del /Q test_tool_simple.py 2>nul

REM Verification and utility scripts
del /Q verify_build_capacity.py 2>nul
del /Q verify_ollama.py 2>nul
del /Q final_verification.py 2>nul
del /Q simulate_bom.py 2>nul
del /Q simulate_new_delay.py 2>nul
del /Q inspect_db.py 2>nul
del /Q list_models.py 2>nul
del /Q force_fix_test.py 2>nul
del /Q reset_log_fresh.py 2>nul

REM Temporary documentation
del /Q AGENT_FIX.md 2>nul
del /Q QUICK_TEST.md 2>nul

REM Cache directory
rmdir /S /Q __pycache__ 2>nul

echo.
echo Cleanup complete!
echo.
pause
