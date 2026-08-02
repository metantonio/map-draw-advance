@echo off
title Compilar Map Draw Advance (.exe)
echo =======================================================
echo          COMPILANDO MAP DRAW ADVANCE A .EXE
echo =======================================================
echo.

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe build_exe.py
) else (
    python build_exe.py
)

echo.
echo Presiona cualquier tecla para salir...
pause > nul
