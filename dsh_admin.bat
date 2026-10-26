@echo off
title JSTM Private Server Admin
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dsh_admin.ps1"
if errorlevel 1 pause
