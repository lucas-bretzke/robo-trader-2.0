@echo off
echo Installing required Python packages...
pip install -U websockets asyncio
pip install -U git+https://github.com/iqoptionapi/iqoptionapi.git
echo Done!
pause
