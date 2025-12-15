@echo off
REM MPV TorBox Launcher
REM Quick launcher for streaming from TorBox

echo ================================================
echo   MPV TorBox Streaming Setup
echo ================================================
echo.
echo 1. Copy your TorBox media link
echo 2. MPV will open shortly
echo 3. Press Ctrl+V to paste the link
echo 4. Press 'i' to show stats
echo 5. Press '?' for help
echo.
echo Starting MPV...
echo.

REM Start MPV
start "" "%~dp0mpv.exe"

timeout /t 2 /nobreak >nul
exit
