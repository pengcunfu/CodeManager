@echo off
set MINIO_PATH=D:\Peng\App\Code\MinIO
start /b %MINIO_PATH%\minio.exe server %MINIO_PATH%\data > minio.log 2>&1
