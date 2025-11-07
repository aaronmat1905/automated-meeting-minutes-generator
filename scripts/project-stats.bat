@echo off
echo ========================================
echo Project Statistics
echo ========================================
echo.
echo Directory Structure:
tree /F /A
echo.
echo File Counts:
dir /S /B *.py | find /C ".py"
echo Python files found
dir /S /B *.md | find /C ".md"
echo Markdown files found
echo.
echo Lines of Code:
powershell -Command "Get-ChildItem -Recurse -Include *.py | Get-Content | Measure-Object -Line"
