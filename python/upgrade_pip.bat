@echo off
echo.
echo Activating virtual environment and updating pip
call venv\Scripts\activate.bat
python.exe -m pip install --upgrade pip
echo.
echo Setup complete. You can now run the application using run.bat
pause