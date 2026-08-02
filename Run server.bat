@echo off
title Map Draw Advance - Web Server
echo =======================================================
echo     INICIANDO SERVIDOR WEB DE MAP DRAW ADVANCE
echo =======================================================
echo.

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe server.py
) else (
    python server.py
)

pause