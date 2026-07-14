@echo off
rem PTT danmaku - desktop overlay version (comments float on top of desktop)
rem no console window; a small control window opens for picking board/article
cd /d %~dp0
where pyw >nul 2>nul && (start "" pyw overlay.pyw & goto :eof)
where pythonw >nul 2>nul && (start "" pythonw overlay.pyw & goto :eof)
start "" py overlay.pyw
