@echo off
cd /d "%~dp0"
python -B news_scraper_gui.py
if errorlevel 1 pause
