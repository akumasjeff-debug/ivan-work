@echo off
rem PTT danmaku - web version (app-mode browser window, port 8003)
cd /d %~dp0

rem start server minimized if not already running
netstat -ano | findstr /r /c:":8003 .*LISTENING" >nul 2>nul
if errorlevel 1 start "ptt-danmaku-server" /min py server.py

rem wait a moment for the server
timeout /t 1 /nobreak >nul

set URL=http://localhost:8003/danmaku.html
set EDGE1=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
set EDGE2=C:\Program Files\Microsoft\Edge\Application\msedge.exe
set CHROME1=C:\Program Files\Google\Chrome\Application\chrome.exe
set CHROME2=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe

if exist "%EDGE1%" (start "" "%EDGE1%" --app=%URL% --window-size=1280,800 & goto :eof)
if exist "%EDGE2%" (start "" "%EDGE2%" --app=%URL% --window-size=1280,800 & goto :eof)
if exist "%CHROME1%" (start "" "%CHROME1%" --app=%URL% --window-size=1280,800 & goto :eof)
if exist "%CHROME2%" (start "" "%CHROME2%" --app=%URL% --window-size=1280,800 & goto :eof)
start "" %URL%
