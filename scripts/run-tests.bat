@echo off
echo Running all tests...
pytest tests/ -v --cov=src --cov-report=html
echo Test report generated in htmlcov/index.html
