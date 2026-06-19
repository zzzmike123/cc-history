@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\CC-History.lnk'); $s.TargetPath='D:\python\pythonw.exe'; $s.Arguments='-m cc_history.app'; $s.WorkingDirectory='D:\tools\cc-history'; $s.IconLocation='D:\tools\cc-history\assets\cc-history-claude-kitty.ico,0'; $s.Save()"
echo Done
