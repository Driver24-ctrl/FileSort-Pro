@echo off
title FileSort Pro - Installation
color 0A

echo.
echo ========================================
echo    FileSort Pro - Installation
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as administrator - Good!
) else (
    echo WARNING: Not running as administrator
    echo Some features may not work properly
    echo.
)

echo Installing FileSort Pro...
echo.

REM Create application directory
if not exist "%PROGRAMFILES%\FileSort Pro" (
    echo Creating application directory...
    mkdir "%PROGRAMFILES%\FileSort Pro"
    echo Directory created: %PROGRAMFILES%\FileSort Pro
) else (
    echo Application directory already exists
)

REM Copy executable
echo Copying application files...
copy "FileSortPro.exe" "%PROGRAMFILES%\FileSort Pro\" >nul
if %errorLevel% == 0 (
    echo FileSortPro.exe copied successfully
) else (
    echo ERROR: Failed to copy FileSortPro.exe
    pause
    exit /b 1
)

REM Copy documentation
if exist "README.md" (
    copy "README.md" "%PROGRAMFILES%\FileSort Pro\" >nul
    echo Documentation copied
)

if exist "LICENSE" (
    copy "LICENSE" "%PROGRAMFILES%\FileSort Pro\" >nul
    echo License copied
)

if exist "PRIVACY_POLICY.md" (
    copy "PRIVACY_POLICY.md" "%PROGRAMFILES%\FileSort Pro\" >nul
    echo Privacy policy copied
)

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\FileSort Pro.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\FileSort Pro\FileSortPro.exe'; $Shortcut.WorkingDirectory = '%PROGRAMFILES%\FileSort Pro'; $Shortcut.Description = 'FileSort Pro - Smart File Organizer'; $Shortcut.Save()}" >nul 2>&1
if %errorLevel% == 0 (
    echo Desktop shortcut created successfully
) else (
    echo WARNING: Failed to create desktop shortcut
)

REM Create start menu shortcut
echo Creating start menu shortcut...
if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\FileSort Pro" (
    mkdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\FileSort Pro"
)
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\FileSort Pro\FileSort Pro.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\FileSort Pro\FileSortPro.exe'; $Shortcut.WorkingDirectory = '%PROGRAMFILES%\FileSort Pro'; $Shortcut.Description = 'FileSort Pro - Smart File Organizer'; $Shortcut.Save()}" >nul 2>&1
if %errorLevel% == 0 (
    echo Start menu shortcut created successfully
) else (
    echo WARNING: Failed to create start menu shortcut
)

REM Create uninstaller
echo Creating uninstaller...
(
echo @echo off
echo title FileSort Pro - Uninstaller
echo color 0C
echo.
echo ========================================
echo    FileSort Pro - Uninstaller
echo ========================================
echo.
echo This will remove FileSort Pro from your system.
echo.
set /p confirm="Are you sure you want to uninstall? (y/N): "
if /i "%%confirm%%" neq "y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)
echo.
echo Removing FileSort Pro...
echo.
REM Remove shortcuts
del "%USERPROFILE%\Desktop\FileSort Pro.lnk" 2>nul
rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\FileSort Pro" 2>nul
REM Remove application files
rmdir /s /q "%PROGRAMFILES%\FileSort Pro" 2>nul
echo.
echo FileSort Pro has been uninstalled.
echo.
pause
) > "%PROGRAMFILES%\FileSort Pro\uninstall.bat"

echo Uninstaller created

echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo FileSort Pro has been installed successfully!
echo.
echo Installation location: %PROGRAMFILES%\FileSort Pro
echo Desktop shortcut: Created
echo Start menu shortcut: Created
echo.
echo You can now launch FileSort Pro from:
echo - Desktop shortcut
echo - Start menu
echo - %PROGRAMFILES%\FileSort Pro\FileSortPro.exe
echo.
echo To uninstall, run: %PROGRAMFILES%\FileSort Pro\uninstall.bat
echo.
echo Thank you for choosing FileSort Pro!
echo.

REM Ask if user wants to launch the application
set /p launch="Would you like to launch FileSort Pro now? (Y/n): "
if /i "%launch%" neq "n" (
    echo Launching FileSort Pro...
    start "" "%PROGRAMFILES%\FileSort Pro\FileSortPro.exe"
)

echo.
echo Installation completed successfully!
pause
