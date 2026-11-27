@echo off
setlocal
cd /d "%~dp0..\..\.."
if defined MRL_PYTHON (
  "%MRL_PYTHON%" "%~dp0MRL_accept_local_v1.py" %*
  exit /b
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0MRL_accept_local_v1.py" %*
  exit /b
)
python "%~dp0MRL_accept_local_v1.py" %*
