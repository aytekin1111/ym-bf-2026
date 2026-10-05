@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [1/2] Veri uretiliyor (poz_index.tsv + poz_veri.h)...
python veri_uret.py
if errorlevel 1 (
  echo VERI URETIMI BASARISIZ. Python ve gerekli kutuphaneler kurulu mu?
  pause
  exit /b 1
)
echo [2/2] Derleniyor...
if exist "H:\mingw64\bin\g++.exe" (
  set "CXX=H:\mingw64\bin\g++.exe"
) else (
  set "CXX=g++"
)
"%CXX%" -O2 -std=c++17 -static -o poz_arama.exe poz_arama.cpp
if errorlevel 1 (
  echo DERLEME BASARISIZ.
  pause
  exit /b 1
)
echo.
echo TAMAM: poz_arama.exe guncellendi.
pause
