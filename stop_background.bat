@echo off
echo Stopping all running OmniTrack background instances...
wmic process where "commandline like '%%main.py watch%%'" call terminate
echo OmniTrack background monitor stopped.
pause
