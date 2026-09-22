@echo off
setlocal
cd /d "%~dp0.."
if "%~1"=="" (
  echo Arrastra sobre este fichero la carpeta que contiene los PNG editados.
  pause
  exit /b 1
)
python tools\export_intro.py --import-dir "%~1" --output-rom "roms_editadas\RockAndCasta-intro.md"
if errorlevel 1 pause
