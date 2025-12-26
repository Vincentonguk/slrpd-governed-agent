@echo off
setlocal

mkdir src 2>nul
mkdir src\slrpd 2>nul
mkdir src\slrpd\api 2>nul
mkdir src\slrpd\execution 2>nul
mkdir src\slrpd\observability 2>nul
mkdir src\slrpd\rag 2>nul
mkdir src\slrpd\state_machine 2>nul

mkdir scripts 2>nul
mkdir contracts 2>nul

mkdir .data 2>nul
mkdir .data\corpus 2>nul
mkdir .data\audit 2>nul
mkdir .data\reports 2>nul

echo Folders OK.
echo.
echo Opening Notepad for key files...
notepad requirements.txt
notepad src\__init__.py
notepad src\slrpd\__init__.py
notepad src\slrpd\config.py
echo.
pause
