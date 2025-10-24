"""
Build script for creating FileSort Pro executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_executable():
    """Build the executable using PyInstaller for Microsoft Store"""
    
    print("Building FileSort Pro executable for Microsoft Store...")
    
    # PyInstaller command optimized for Microsoft Store
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=FileSortPro",
        "--icon=icon.ico",  # You'll need to add an icon file
        "--add-data=README.md;.",
        "--add-data=LICENSE;.",
        "--add-data=PRIVACY_POLICY.md;.",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui", 
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=winreg",
        "--hidden-import=json",
        "--hidden-import=logging",
        "--hidden-import=threading",
        "--hidden-import=datetime",
        "--hidden-import=pathlib",
        "--hidden-import=subprocess",
        "--hidden-import=shutil",
        "--hidden-import=os",
        "--hidden-import=sys",
        "--hidden-import=time",
        "--clean",
        "--noconfirm",
        "filesort.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("SUCCESS: Executable built successfully!")
        
        # Move executable to root directory
        exe_path = Path("dist/FileSortPro.exe")
        if exe_path.exists():
            shutil.move(str(exe_path), "FileSortPro.exe")
            print("SUCCESS: Executable moved to root directory")
        
        # Clean up build files
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        if os.path.exists("FileSortPro.spec"):
            os.remove("FileSortPro.spec")
            
        print("SUCCESS: Build files cleaned up")
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Build failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False
    
    return True

def create_installer():
    """Create a simple installer script"""
    
    installer_script = """
@echo off
echo Installing FileSort Pro...
echo.

REM Create application directory
if not exist "%PROGRAMFILES%\\FileSort Pro" mkdir "%PROGRAMFILES%\\FileSort Pro"

REM Copy executable
copy "FileSortPro.exe" "%PROGRAMFILES%\\FileSort Pro\\"

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\FileSort Pro.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\\FileSort Pro\\FileSortPro.exe'; $Shortcut.Save()"

REM Create start menu shortcut
echo Creating start menu shortcut...
if not exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\FileSort Pro" mkdir "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\FileSort Pro"
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\FileSort Pro\\FileSort Pro.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\\FileSort Pro\\FileSortPro.exe'; $Shortcut.Save()"

echo.
echo ✅ FileSort Pro installed successfully!
echo You can now launch it from the Start menu or desktop shortcut.
pause
"""
    
    with open("install.bat", "w") as f:
        f.write(installer_script)
    
    print("SUCCESS: Installer script created: install.bat")

if __name__ == "__main__":
    print("FileSort Pro Build Script")
    print("=" * 40)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("SUCCESS: PyInstaller found")
    except ImportError:
        print("ERROR: PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build executable
    if build_executable():
        create_installer()
        print("\nSUCCESS: Build completed successfully!")
        print("Files created:")
        print("- FileSortPro.exe (main executable)")
        print("- install.bat (installer script)")
        print("- README.md (documentation)")
        print("- LICENSE (license file)")
    else:
        print("\nERROR: Build failed. Please check the error messages above.")
        sys.exit(1)
