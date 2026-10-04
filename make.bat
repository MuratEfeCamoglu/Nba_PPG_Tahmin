@echo off
REM make sarmalayicisi (Windows cmd/PowerShell): Makefile hedeflerini mini_make.py ile calistirir.
if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" "%~dp0mini_make.py" %*
) else (
  python "%~dp0mini_make.py" %*
)
exit /b %ERRORLEVEL%
