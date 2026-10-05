@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Poz Arama baslatiliyor...
python poz_arama_gui.py
echo.
echo ----------------------------------------
echo Program kapandi. Cikis kodu: %ERRORLEVEL%
echo Eger yukarida hata yaziyorsa lutfen fotografini/metnini paylasin.
pause
