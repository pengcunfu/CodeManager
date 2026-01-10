@echo off
rem if "%1"=="h" goto begin
rem start mshta vbscript:createobject("wscript.shell").run("""%~nx0"" h",0)(window.close)&&exit
rem :begin

cd /d D:\Peng\App\DevApp\Redis
redis-server

echo Redis服务已启动