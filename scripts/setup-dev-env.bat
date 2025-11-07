@echo off
echo Setting up development environment...
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo Development environment ready!
echo Run 'venv\Scripts\activate' to activate the environment
