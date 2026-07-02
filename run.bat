@echo off
REM ===================================================================
REM  Launcher for Windows.
REM
REM  Creates a local virtual environment on first run, installs the
REM  dependencies (yfinance, matplotlib) into it, then starts the
REM  Stock Price Viewer. Double-click this file to run it.
REM
REM  This window ALWAYS waits for a key press before closing, so it can
REM  never just flash open and shut: whatever happens, you can read it.
REM ===================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Stock Price Viewer

REM --- 1. Is a *working* Python available? ---------------------------
call :find_python
if not defined PYLAUNCH (
    echo Python 3 was not found on this computer.
    echo Please install it from https://www.python.org/downloads/
    echo and tick "Add Python to PATH", then run this file again.
    goto end
)
echo Using Python: %PYLAUNCH%

%PYLAUNCH% -c "import tkinter" >nul 2>nul
if not "!errorlevel!"=="0" (
    echo Python is installed but Tkinter is missing, so the window
    echo cannot open. Re-run the Python installer and make sure
    echo "tcl/tk and IDLE" is selected, then run this file again.
    goto end
)

REM --- 2. Virtual environment + dependencies (first run only) --------
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PYLAUNCH% -m venv .venv
    if not "!errorlevel!"=="0" (
        echo Could not create the virtual environment.
        goto end
    )
)

".venv\Scripts\python.exe" -c "import yfinance, matplotlib" >nul 2>nul
if not "!errorlevel!"=="0" (
    echo Installing dependencies - first run only, this may take a minute...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if not "!errorlevel!"=="0" (
        echo.
        echo Installing the dependencies failed. Check your internet
        echo connection and run this file again.
        goto end
    )
)

REM --- 3. Run the app --------------------------------------------------
echo Starting Stock Price Viewer...
".venv\Scripts\python.exe" main.py
set "EXITCODE=!errorlevel!"
echo.
echo The app has closed ^(exit code %EXITCODE%^).
if not "%EXITCODE%"=="0" echo If a Python error is shown above, please report it.
goto end

REM ===================================================================
REM  Helper: locate a Python that can actually RUN code, store it in
REM  PYLAUNCH. We don't trust the command merely existing, because
REM  Windows ships a fake "python.exe" App-Execution-Alias stub that
REM  runs nothing. So we make Python PRINT a known value and only
REM  accept it if that value actually comes back: the stub prints
REM  nothing, a real interpreter prints "42".
REM ===================================================================
:find_python
set "PYLAUNCH="
call :verify "py -3"
if defined PYLAUNCH exit /b
call :verify "python"
if defined PYLAUNCH exit /b
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if not defined PYLAUNCH if exist "%%D\python.exe" (
        for /f "delims=" %%v in ('"%%D\python.exe" -c "print(42)" 2^>nul') do (
            if "%%v"=="42" set PYLAUNCH="%%D\python.exe"
        )
    )
)
exit /b

:verify
REM %~1 is a python command. Set PYLAUNCH to it only if it really runs.
set "PYOUT="
for /f "delims=" %%v in ('%~1 -c "print(42)" 2^>nul') do set "PYOUT=%%v"
if "%PYOUT%"=="42" set "PYLAUNCH=%~1"
exit /b

REM ===================================================================
REM  Single place EVERY path lands on (success or failure) so the
REM  window always pauses and never flashes shut.
REM ===================================================================
:end
echo.
pause
exit /b
