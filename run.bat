@echo off

echo Installing requirements...
pip install -r requirements.txt

cls

echo Starting Cloud Checker v8 in 2 seconds...
timeout /t 2

py cloud_checker_v8.py
