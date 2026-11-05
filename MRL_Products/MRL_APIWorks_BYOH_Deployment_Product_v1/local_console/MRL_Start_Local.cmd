@echo off
setlocal
cd /d "%~dp0..\..\.."
if defined MRL_PYTHON (
  "%MRL_PYTHON%" "%~dp0MRL_local_console_v1.py" %*
  exit /b
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0MRL_local_console_v1.py" %*
  exit /b
)
where python >nul 2>nul
if not errorlevel 1 (
  python "%~dp0MRL_local_console_v1.py" %*
  exit /b
)
echo Python 3.10+ was not found. Set MRL_PYTHON to your python.exe path.
pause
exit /b 2
