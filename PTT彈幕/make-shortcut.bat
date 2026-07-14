@echo off
rem create desktop shortcut "PTT Danmaku" pointing to start.bat
powershell -NoProfile -Command "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\PTT Danmaku.lnk'); $s.TargetPath='%~dp0start.bat'; $s.WorkingDirectory='%~dp0'; $s.Save(); Write-Output 'shortcut created'"
pause
