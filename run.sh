#!/usr/bin/env bash
# ===================================================================
#  Launcher for Linux and macOS.
#
#  Creates a local virtual environment on first run, installs the
#  dependencies (yfinance, matplotlib) into it, then starts the app.
#
#  Run it from a terminal:   ./run.sh
#  (If it is not executable yet:   chmod +x run.sh )
# ===================================================================
set -u
cd "$(dirname "$0")"

have() { command -v "$1" >/dev/null 2>&1; }

# --- 1. Locate a working Python 3 -----------------------------------
if have python3 && python3 -c 'import sys' >/dev/null 2>&1; then
    PY=python3
elif have python && python -c 'import sys; exit(0 if sys.version_info[0]==3 else 1)' >/dev/null 2>&1; then
    PY=python
else
    echo "Python 3 was not found. Install it first:"
    echo "  Debian/Ubuntu/Kali:  sudo apt install python3 python3-venv python3-tk"
    echo "  Fedora:              sudo dnf install python3 python3-tkinter"
    echo "  macOS:               brew install python python-tk"
    exit 1
fi

# --- 2. Tkinter is needed for the window ----------------------------
if ! "$PY" -c 'import tkinter' >/dev/null 2>&1; then
    echo "Python is installed but tkinter is missing, so no window can open."
    echo "  Debian/Ubuntu/Kali:  sudo apt install python3-tk"
    echo "  Fedora:              sudo dnf install python3-tkinter"
    echo "  macOS:               brew install python-tk"
    exit 1
fi

# --- 3. Virtual environment + dependencies (first run only) ---------
if [ ! -x .venv/bin/python ]; then
    echo "Creating virtual environment..."
    "$PY" -m venv .venv || exit 1
fi

if ! .venv/bin/python -c 'import yfinance, matplotlib' >/dev/null 2>&1; then
    echo "Installing dependencies - first run only..."
    .venv/bin/python -m pip install -r requirements.txt || exit 1
fi

# --- 4. Run ----------------------------------------------------------
echo "Starting Stock Price Viewer..."
exec .venv/bin/python stock_viewer.py
