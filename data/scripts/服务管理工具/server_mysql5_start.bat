@echo off
rem if "%1"=="h" goto begin
start mshta vbscript:createobject("wscript.shell").run("""%~nx0"" h",0)(window.close)&&exit
rem :begin

cd /d D:\Peng\App\DevApp\phpstudy_pro\Extensions\MySQL5.7.26\bin
mysqld --standalone
