@echo off
title AutoScout Pro - Ikinci El Arac Ilan Arama
color 0A
echo.
echo ================================================================
echo          ___         _     ____             __  _              
echo         /   | __  __(_) __/ __ \____ ______/ /_(_)___  ____ _ 
echo        / /| |/ / / / // /_/ / / / __ `/ ___/ __/ / __ \/ __ `/ 
echo       / ___ / /_/ / // /_/ /_/ / /_/ / /__/ /_/ / / / / /_/ /  
echo      /_/  |_\__, /_//_/  \___\_\__,_/\___/\__/_/_/ /_/\__, /   
echo             /____/    Pro                               /____/    
echo.
echo ================================================================
echo    Ikinci El Arac Ilan Arama Platformu
echo ================================================================
echo.

cd /d "%~dp0"

:: Python kontrolü
echo [1/3] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python yuklu degil! Lutfen Python 3.8+ yukleyin.
    echo        https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

:: Sanal ortam kontrolü
echo [2/3] Sanal ortam kontrol ediliyor...
if not exist "venv" (
    echo    Sanal ortam olusturuluyor...
    python -m venv venv
    echo    Sanal ortam olusturuldu.
) else (
    echo    Sanal ortam mevcut.
)
echo.

:: Sanal ortamı aktifleştir
call venv\Scripts\activate.bat

:: Bağımlılıkları yükle
echo [3/3] Bagimliliklar kontrol ediliyor...
pip install -r requirements.txt -q
echo    Bagimliliklar hazir.
echo.

:: Uygulamayı başlat
echo ================================================================
echo    Uygulama baslatiliyor...
echo    Adres: http://localhost:5000
echo    Durdurmak icin CTRL+C basin
echo ================================================================
echo.

python app.py

pause
