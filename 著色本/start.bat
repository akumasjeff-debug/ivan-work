@echo off
cd /d "%~dp0"
title Coloring Book - close this window to stop the server

set "PY=C:\Users\IVAN\AppData\Local\Programs\Python\Python311\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================================
echo            Coloring Book  (line art colorizer)
echo   URL : http://localhost:8001/coloring.html
echo   Close this BLACK window  =  stop the server
echo   (Open the URL in Chrome or Edge)
echo ============================================================
echo.
echo Starting server... browser opens automatically in ~2 seconds
echo.

start "" /b powershell -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8001/coloring.html'"

"%PY%" -m http.server 8001

echo.
echo ============================================================
echo  Server stopped, or failed to start (see message above).
echo  If you see "address already in use": port 8001 is busy,
echo  change 8001 to 8081 in this file (two places) and retry.
echo ============================================================
pause >nul
