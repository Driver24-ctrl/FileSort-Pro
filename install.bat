
@echo off
echo Installing FileSort Pro...
echo.

REM Create application directory
if not exist "%PROGRAMFILES%\FileSort Pro" mkdir "%PROGRAMFILES%\FileSort Pro"

REM Copy executable
copy "FileSortPro.exe" "%PROGRAMFILES%\FileSort Pro\"

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\FileSort Pro.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\FileSort Pro\FileSortPro.exe'; $Shortcut.Save()"

REM Create start menu shortcut
echo Creating start menu shortcut...
if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\FileSort Pro" mkdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\FileSort Pro"
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\FileSort Pro\FileSort Pro.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\FileSort Pro\FileSortPro.exe'; $Shortcut.Save()"

echo.
echo SUCCESS: FileSort Pro installed successfully!
echo You can now launch it from the Start menu or desktop shortcut.
pause
