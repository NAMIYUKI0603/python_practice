@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo テキストマイニングアプリを起動しています...

:: Pythonのパスを指定してStreamlitを起動
set "PYTHON_CMD=C:\Users\t.namigata\AppData\Local\Python\bin\python.exe"

if exist "%PYTHON_CMD%" (
    "%PYTHON_CMD%" -m streamlit run app.py
) else (
    echo 指定されたPythonが見つからないため、通常のコマンドで起動を試みます...
    python -m streamlit run app.py
)

pause
