@echo off
chcp 65001 >nul
title Learning English — HTTPS Server (Voice)

cd /d "%~dp0"

echo.
echo  กำลังเปิด HTTPS server สำหรับ Voice / ไมค์...
echo  (ถ้า Whisper error — ปิดหน้าต่าง server เก่าก่อน Ctrl+C แล้วรันใหม่)
echo.

python scripts\local_server.py --https

if errorlevel 1 (
  echo.
  echo  [ERROR] เปิด HTTPS server ไม่ได้
  pause
)
