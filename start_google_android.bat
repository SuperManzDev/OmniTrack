@echo off
title Google Android Emulator (OmniSnapDevice)
set ANDROID_SDK_ROOT=C:\Users\MNZ\AppData\Local\Android\Sdk
set PATH=%ANDROID_SDK_ROOT%\emulator;%ANDROID_SDK_ROOT%\platform-tools;%PATH%

echo Starting Google Official Android Virtual Device 'OmniSnapDevice'...
emulator.exe -avd OmniSnapDevice -netdelay none -netspeed full
pause
