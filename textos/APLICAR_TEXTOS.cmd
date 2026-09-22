@echo off
setlocal
cd /d "%~dp0.."
if "%~1"=="" goto usage
if not exist "roms_editadas" mkdir "roms_editadas"
python tools\export_texts.py --import-file "%~1" --output-rom "roms_editadas\textos_editados_%RANDOM%_%RANDOM%.md"
pause
exit /b %errorlevel%
:usage
echo Arrastra textos_editados.json sobre este CMD.
pause
exit /b 1
