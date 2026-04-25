#!/bin/bash
# AutoScout Pro - Başlatma Scripti (Linux/Mac)

echo ""
echo "================================================================"
echo "         ___         _     ____             __  _              "
echo "        /   | __  __(_) __/ __ \____ ______/ /_(_)___  ____ _ "
echo "       / /| |/ / / / // /_/ / / / __ \` / ___/ __/ / __ \/ __ \`/ "
echo "      / ___ / /_/ / // /_/ /_/ / /_/ / /__/ /_/ / / / / /_/ /  "
echo "     /_/  |_\__, /_//_/  \___\_\__,_/\___/\__/_/_/ /_/\__, /   "
echo "            /____/    Pro                               /____/    "
echo ""
echo "================================================================"
echo "   İkinci El Araç İlan Arama Platformu"
echo "================================================================"
echo ""

# Dizin değiştir
cd "$(dirname "$0")"

# Python kontrolü
echo "[1/3] Python kontrol ediliyor..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[HATA] Python yüklü değil! Lütfen Python 3.8+ yükleyin."
        exit 1
    fi
    PYTHON_CMD=python
else
    PYTHON_CMD=python3
fi
$PYTHON_CMD --version
echo ""

# Sanal ortam
echo "[2/3] Sanal ortam kontrol ediliyor..."
if [ ! -d "venv" ]; then
    echo "   Sanal ortam oluşturuluyor..."
    $PYTHON_CMD -m venv venv
    echo "   Sanal ortam oluşturuldu."
else
    echo "   Sanal ortam mevcut."
fi
echo ""

# Aktifleştir ve bağımlılıkları yükle
source venv/bin/activate
echo "[3/3] Bağımlılıklar kontrol ediliyor..."
pip install -r requirements.txt -q
echo "   Bağımlılıklar hazır."
echo ""

echo "================================================================"
echo "   Uygulama başlatılıyor..."
echo "   Adres: http://localhost:5000"
echo "   Durdurmak için CTRL+C basın"
echo "================================================================"
echo ""

python app.py
