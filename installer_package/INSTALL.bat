@echo off
:: Nivya Dark Net Installer
:: Simple installation script

echo ========================================
echo   Nivya Dark Net - Installation
echo ========================================
echo.

set "INSTALL_DIR=%ProgramFiles%\Nivya Dark Net"

echo Installing to: %INSTALL_DIR%
echo.

:: Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Copy executable
echo Copying files...
copy /Y "NivyaDarkNet.exe" "%INSTALL_DIR%\NivyaDarkNet.exe"

:: Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\Nivya Dark Net.lnk'); $s.TargetPath = '%INSTALL_DIR%\NivyaDarkNet.exe'; $s.Save()"

:: Create start menu shortcut
echo Creating start menu shortcut...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Nivya Dark Net.lnk'); $s.TargetPath = '%INSTALL_DIR%\NivyaDarkNet.exe'; $s.Save()"

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Launch Nivya Dark Net from your desktop or start menu.
echo.
pause
