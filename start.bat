@echo off
cd /d "%~dp0"
title Image Compositor - close this window to stop the server

set "PY=C:\Users\IVAN\AppData\Local\Programs\Python\Python311\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo            Image Compositor  (image compositor)
echo   URL : http://localhost:8000/compositor.html
echo   Close this BLACK window  =  stop the server
echo   (Open the URL in Chrome or Edge)
echo ============================================================
echo.
echo Starting server... browser opens automatically in ~2 seconds
echo.

start "" /b powershell -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8000/compositor.html'"

"%PY%" -m http.server 8000

echo.
echo ============================================================
echo  Server stopped, or failed to start (see message above).
echo  If you see "address already in use": port 8000 is busy,
echo  change 8000 to 8080 in this file (two places) and retry.
echo ============================================================
pause >nul
