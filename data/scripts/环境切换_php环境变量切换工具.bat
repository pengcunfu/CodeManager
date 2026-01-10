@echo off
rem 请求管理员权限
(pushd "%~dp0") && (reg query "HKU\S-1-5-19" > nul 2>&1) || (powershell -command "& { Start-Process '%~sdpnx0' -Verb RunAs }" && exit)
setlocal enabledelayedexpansion

rem 设置基础路径的 Node.js 路径
set "basePath=D:\Peng\App\DevApp\node"

rem 尝试执行 node -v 命令
node -v > nul 2>&1
if %errorlevel% neq 0 (
    rem 执行失败
	echo 当前没有配置Node环境
	echo.
) else (
	rem 执行成功
	for /f "tokens=* delims=" %%i in ('node -v') do set "currentVersion=%%i"
    set "currentVersion=!currentVersion:~1!"
	echo 当前Node环境版本：[!currentVersion!]
	echo.
)

rem 提示用户选择 Node.js 版本
echo 请选择Nodejs环境：
echo.
echo  【1】版本[12.12.0]
echo.
echo  【2】版本[16.13.2]
echo.
echo  【3】版本[18.18.2]
echo.
echo  【4】版本[20.10.0]
echo.

set /p choice=请选择版本: 
echo.

rem 根据用户选择设置 Node.js 版本
if "%choice%" equ "1" set version=12.12.0
if "%choice%" equ "2" set version=16.13.2
if "%choice%" equ "3" set version=18.18.2
if "%choice%" equ "4" set version=20.10.0

set "nodejs=!basePath!!version!"

rem 尝试执行 node -v 命令
node -v > nul 2>&1
if %errorlevel% neq 0 (
    rem 执行 node -v 报错，添加路径到 PATH
    set "PATH=!PATH!;%nodejs%"
	
	rem 更新系统环境变量
	setx PATH "!PATH!" /M
    echo 已添加到 PATH: !nodejs!
	echo.
) else (
    rem 执行 node -v 成功，比较版本号
    for /f "tokens=* delims=" %%i in ('node -v') do set "currentVersion=%%i"
    set "currentVersion=!currentVersion:~1!"

    if "!currentVersion!" equ "!version!" (
        echo Node.js 版本号: !version!
        echo 版本相同，不需要修改 PATH。
		echo.
    ) else (
        rem 版本不相同，删除旧版本并添加当前版本
        set "PATH=!PATH:%basePath%12.12.0%=!"
        set "PATH=!PATH:%basePath%16.13.2%=!"
        set "PATH=!PATH:%basePath%18.18.2%=!"
        set "PATH=!PATH:%basePath%20.10.0%=!"

        set "PATH=!PATH!;%nodejs%"

        echo 删除旧版本[!currentVersion!]，添加新版本[!version!]
		
		rem 更新系统环境变量
		setx PATH "!PATH!" /M
		echo 已添加到 PATH: [!nodejs!]
		echo.
    )
)

rem 显示当前 Node.js 版本
node -v > nul 2>&1
if %errorlevel% neq 0 (
    rem 执行失败
	echo 没有配置成功！
) else (
	rem 执行成功
	for /f "tokens=* delims=" %%i in ('node -v') do set "currentVersion=%%i"
    set "currentVersion=!currentVersion:~1!"
	echo 当前版本：[!currentVersion!]
)

echo.
rem 暂停，等待用户按下任意键后退出
pause

endlocal

