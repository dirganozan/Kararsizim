#!/bin/bash

# Build script for Vercel Serverless Deployment
echo "--> Bağımlılıklar yükleniyor..."
python3 -m pip install -r requirements.txt

echo "--> Statik dosyalar derleniyor (collectstatic)..."
python3 manage.py collectstatic --noinput --clear

echo "--> Build başarıyla tamamlandı!"
