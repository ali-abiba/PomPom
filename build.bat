@echo off
echo Building PomPom Application...

:: Create version variable
set VERSION=1.0.0

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt

:: Clean previous builds
echo Cleaning previous builds...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "PomPom.spec" del "PomPom.spec"

:: Build executable
echo Building executable...
python -m PyInstaller --name="PomPom" --icon=icon.ico --add-data="icon.ico;." --noconsole --onefile main.py

:: Create distribution directory
echo Creating distribution package...
set DIST_DIR=PomPom-v%VERSION%
if exist "%DIST_DIR%" rd /s /q "%DIST_DIR%"
mkdir "%DIST_DIR%"

:: Copy files to distribution directory
echo Copying files...
copy "dist\PomPom.exe" "%DIST_DIR%"
copy "icon.ico" "%DIST_DIR%"
copy "README.md" "%DIST_DIR%"

:: Create ZIP file
echo Creating ZIP archive...
powershell Compress-Archive -Path "%DIST_DIR%" -DestinationPath "%DIST_DIR%.zip" -Force

echo Build complete!
echo Executable: %DIST_DIR%\PomPom.exe
echo ZIP archive: %DIST_DIR%.zip

pause 