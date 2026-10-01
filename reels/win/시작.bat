@echo off
chcp 65001 >nul
echo.
echo  릴스 편집 도구 - 설치하고 점검합니다
echo  끝나면 바탕화면에 "릴스-점검결과.txt" 가 생깁니다.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-and-check.ps1"
echo.
echo  끝났습니다. 바탕화면의 "릴스-점검결과.txt" 를 보내주세요.
pause
