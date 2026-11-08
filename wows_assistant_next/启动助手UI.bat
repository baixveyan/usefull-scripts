@echo off
cd /d "%~dp0"
"D:\coder\anaconda\envs\scripts\Scripts\wows-assistant.exe" launcher-ui
if errorlevel 1 pause
