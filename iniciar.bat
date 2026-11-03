@echo off
setlocal enabledelayedexpansion
title Restaurante El Filete - Sistema POS y Servidor

echo =====================================================================
echo           RESTAURANTE "EL FILETE" - INICIADOR DEL SISTEMA
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. Deteccion del ejecutable de Python
set "PY_CMD="

:: Metodo A: Comando python en el PATH
where python >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    goto :PYTHON_ENCONTRADO
)

:: Metodo B: Lanzador oficial py en el PATH
where py >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py"
    goto :PYTHON_ENCONTRADO
)

:: Metodo C: Rutas estandar de instalacion de Python en Windows
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD=%%D\python.exe"
        goto :PYTHON_ENCONTRADO
    )
)
for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD=%%D\python.exe"
        goto :PYTHON_ENCONTRADO
    )
)

:PYTHON_ENCONTRADO
if "%PY_CMD%"=="" (
    echo [ERROR CRITICO] No se encontro ninguna instalacion valida de Python.
    echo.
    echo Por favor asegurese de:
    echo  1. Tener Python 3.8 o superior instalado en el equipo.
    echo  2. Haber marcado la opcion "Add python.exe to PATH" durante la instalacion.
    echo  3. Descargar Python desde: https://www.python.org/downloads/
    echo.
    echo Presione cualquier tecla para salir...
    pause >nul
    exit /b 1
)

echo [OK] Interprete de Python detectado: %PY_CMD%
echo.

:: 2. Verificacion y creacion automatica de la base de datos si no existe
if not exist "%~dp0Filete2.db" (
    echo [AVISO] No se detecto la base de datos 'Filete2.db'.
    echo [INFO] Creando e inicializando tablas y datos semilla por primera vez...
    "%PY_CMD%" "%~dp0init_db.py" --force
    if errorlevel 1 (
        echo.
        echo [ERROR] Ocurrio un fallo al inicializar la base de datos 'Filete2.db'.
        echo Revise el mensaje de error anterior.
        echo.
        pause
        exit /b 1
    )
    echo [OK] Base de datos 'Filete2.db' inicializada satisfactoriamente.
    echo.
) else (
    echo [OK] Base de datos 'Filete2.db' verificada.
)

:: 3. Apertura del navegador con la aplicacion web
echo [INFO] Abriendo la aplicacion en el navegador predeterminado...
start http://localhost:5000

:: 4. Inicio del servidor Backend
echo [INFO] Iniciando el servidor backend (server.py)...
echo Para detener el sistema, presione CTRL + C o cierre esta ventana.
echo.

"%PY_CMD%" "%~dp0server.py"

if errorlevel 1 (
    echo.
    echo [ERROR] El servidor backend se detuvo inesperadamente con codigo de error %errorlevel%.
    pause
)

endlocal
