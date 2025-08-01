@echo off
echo Creating Python virtual environment in 'venv'...
python -m venv venv
echo.
echo Activating virtual environment and installing dependencies from requirements.txt...
call venv\Scripts\activate.bat
REM upgrade pip
python.exe -m pip install --upgrade pip
REM install ndi-python from wheel (see it's issue #40)
pip install ndi/ndi_python-5.1.1.5-cp312-cp312-win_amd64.whl
REM then do the requirements 
pip install -r requirements.txt
echo.
echo Setup complete. You can now run the application using run.bat
pause