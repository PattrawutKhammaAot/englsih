@echo off
chcp 65001 >nul
title Learning English — Local Server

cd /d "%~dp0"

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  set "IP=%%a"
  goto :found_ip
)
:found_ip
set "IP=%IP:~1%"

echo.
echo  ========================================
echo   Learning English — LAN Server
echo  ========================================
echo.
echo   เปิดเซิร์ฟเวอร์ที่พอร์ต 8080...
echo   ปิดได้ด้วย Ctrl+C
echo.
echo   เครื่องนี้:     http://localhost:8080
if defined IP echo   เครื่องอื่นใน WiFi: http://%IP%:8080
echo.
echo   แผนเรียน:  /index.html
echo   AI Tutor:  /ai.html  (มี AI Proxy สำหรับ MaxPlus)
echo.
echo   สำหรับ Voice/ไมค์ ใช้ start-server-https.bat แทน (HTTPS)
echo.
echo  ========================================
echo.

python scripts\local_server.py

if errorlevel 1 (
  echo.
  echo  [ERROR] เปิด server ไม่ได้ — ตรวจว่ามี Python ติดตั้งแล้ว
  pause
)
