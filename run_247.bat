@echo off
title OmniTrack 24/7 Package Monitor
cd /d "C:\Users\MNZ\package-tracker"
:loop
echo [%date% %time%] Starting OmniTrack (Hourly Polling)...
python main.py watch --interval 60
echo [%date% %time%] OmniTrack stopped or restarted. Re-launching in 10 seconds...
timeout /t 10
goto loop
