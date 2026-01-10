@echo off
chcp 65001

REM 检查是否存在MinIO服务器的进程
tasklist | find /i "minio.exe" > nul
if errorlevel 1 (
    echo MinIO服务器未在后台运行
) else (
    REM 结束MinIO服务器的进程
    taskkill /F /IM minio.exe > nul
    echo MinIO服务器已成功停止
)

pause
