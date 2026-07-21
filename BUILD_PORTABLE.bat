@echo off
chcp 65001 > nul
title Zombie Tower Defense - Build v1.5.3

set VERSION=1.5.3

echo ============================================
echo    🧟 ZOMBIE TOWER DEFENSE v%VERSION%
echo    СБОРКА PORTABLE-ВЕРСИИ
echo ============================================
echo.

:: Проверяем наличие Python
echo [1/6] Проверка Python...
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python и добавьте в PATH.
    pause
    exit /b 1
) else (
    python --version
    echo ✅ Python найден
)

:: Проверяем/устанавливаем PyInstaller
echo.
echo [2/6] Установка/обновление PyInstaller...
python -m pip install --upgrade pyinstaller > nul 2>&1
if errorlevel 1 (
    echo ❌ Ошибка установки PyInstaller!
    pause
    exit /b 1
) else (
    echo ✅ PyInstaller установлен
)

:: Проверяем зависимости игры (pygame, moderngl, numpy)
echo.
echo [3/6] Проверка зависимостей игры...
python -c "import pygame" > nul 2>&1
if errorlevel 1 (
    echo ⚠️ Pygame не найден. Устанавливаю...
    python -m pip install pygame==2.5.2
)
python -c "import moderngl" > nul 2>&1
if errorlevel 1 (
    echo ⚠️ ModernGL не найден. Устанавливаю...
    python -m pip install moderngl==5.12.0
)
python -c "import numpy" > nul 2>&1
if errorlevel 1 (
    echo ⚠️ NumPy не найден. Устанавливаю...
    python -m pip install numpy
)
echo ✅ Зависимости: pygame, moderngl, numpy

:: Очистка
echo.
echo [4/6] Очистка старых сборок...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul
if exist "portable" rmdir /s /q "portable" 2>nul
echo ✅ Очищено

:: Сборка
echo.
echo [5/6] Сборка EXE (это может занять несколько минут)...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "ZombieTowerDefense" ^
    --add-data "assets;assets" ^
    --add-data "data;data" ^
    --add-data "settings.json;." ^
    --hidden-import "pygame" ^
    --hidden-import "moderngl" ^
    --hidden-import "glcontext" ^
    --hidden-import "numpy" ^
    --hidden-import "sqlite3" ^
    --collect-all "pygame" ^
    --collect-all "moderngl" ^
    --collect-all "glcontext" ^
    main.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка при сборке!
    pause
    exit /b 1
)

:: Портативная версия
echo.
echo [6/6] Создание портативной версии...
mkdir "portable" 2>nul

if exist "dist\ZombieTowerDefense.exe" (
    copy "dist\ZombieTowerDefense.exe" "portable\ZombieTowerDefense.exe" > nul
    echo ✅ EXE скопирован
) else (
    echo ❌ EXE не найден в dist!
    pause
    exit /b 1
)

:: Ассеты и данные рядом с EXE (игра читает их из рабочей папки)
xcopy "assets" "portable\assets" /E /I /Y /Q > nul
echo ✅ Assets скопированы

xcopy "data" "portable\data" /E /I /Y /Q > nul
:: Убираем кэш питона из data
for /d /r "portable\data" %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
echo ✅ Data скопированы

:: Чистые папки сейвов (без локального прогресса разработчика)
mkdir "portable\saves" 2>nul
mkdir "portable\saves\profiles" 2>nul
echo ✅ Чистые saves созданы

copy "settings.json" "portable\settings.json" > nul 2>&1
echo ✅ settings.json скопирован

:: Документация
if exist "README.md" copy "README.md" "portable\README.md" > nul
if exist "CHANGELOG.md" copy "CHANGELOG.md" "portable\CHANGELOG.md" > nul
echo ✅ Документация скопирована

:: run.bat
(
echo @echo off
echo title Zombie Tower Defense v%VERSION%
echo start "" "ZombieTowerDefense.exe"
echo exit
) > "portable\run.bat"
echo ✅ run.bat создан

:: ZIP
echo.
echo Создание ZIP архива...
if exist "ZombieTowerDefense_v%VERSION%.zip" del "ZombieTowerDefense_v%VERSION%.zip" 2>nul
powershell -Command "Compress-Archive -Path portable\* -DestinationPath ZombieTowerDefense_v%VERSION%.zip -Force" 2>nul
if exist "ZombieTowerDefense_v%VERSION%.zip" (
    echo ✅ ZIP архив создан: ZombieTowerDefense_v%VERSION%.zip
) else (
    echo ⚠️ ZIP не создан
)

echo.
echo ============================================
echo    ✅ СБОРКА v%VERSION% ЗАВЕРШЕНА!
echo ============================================
echo.
echo 📁 Портативная версия: portable\
echo 📦 ZIP архив: ZombieTowerDefense_v%VERSION%.zip
echo.
echo Для запуска: portable\ZombieTowerDefense.exe
echo Требуется видеокарта с OpenGL 3.3+
echo.
pause
