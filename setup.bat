@echo off
echo ==========================================
echo  ContextLLM Pro - Windows Setup
echo ==========================================
echo.

:: Check if Python is installed - try py launcher first
py --version >nul 2>&1
if errorlevel 1 (
    :: Try direct python command
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python is not installed or not in PATH!
        echo.
        echo 📥 Install Python from:
        echo    https://python.org/downloads/
        echo    ✅ Make sure to check "Add Python to PATH"
        echo.
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=py
)

echo ✅ Python detected
echo.

:: Install requirements
echo 🔧 Installing dependencies...

:: Try user install first (safer method)
%PYTHON_CMD% -m pip install --user -r requirements.txt

if errorlevel 1 (
    echo ⚠️ User install failed, trying alternatives...
    echo.
    echo 🔧 Alternative solutions:
    echo    1. Manual install: %PYTHON_CMD% -m pip install --user PyQt6 requests tiktoken
    echo    2. Run as administrator and try again
    echo    3. Use virtual environment:
    echo       %PYTHON_CMD% -m venv venv
    echo       venv\Scripts\activate
    echo       pip install -r requirements.txt
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Dependencies installed successfully (user mode)!
)

echo.
echo 🎉 Setup completed successfully!
echo.
echo 📋 Next steps:
echo    %PYTHON_CMD% main.py
echo.
echo 💡 For GitHub token (optional):
echo    set GITHUB_TOKEN=your_token_here
echo.
echo ⭐ If you like this project, please star it on GitHub!
echo.
pause 