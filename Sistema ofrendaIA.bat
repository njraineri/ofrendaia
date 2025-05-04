@echo off
cd C:\ofrendaia
start python app.py
timeout /t 3 /nobreak
start http://127.0.0.1:5000
exit
