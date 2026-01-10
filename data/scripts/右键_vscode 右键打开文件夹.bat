@ECHO OFF&(PUSHD "%~DP0")&(REG QUERY "HKU\S-1-5-19">NUL 2>&1)||(
powershell -Command "Start-Process '%~sdpnx0' -Verb RunAs"&&EXIT)

REM 这段批处理脚本的目的是检查脚本是否以管理员权限运行，如果没有管理员权限，则尝试以管理员权限重新运行脚本。

VER|FINDSTR "5\.[0-9]\.[0-9][0-9]*" > NUL && (
ECHO.&ECHO 当前版本不支持WinXP &PAUSE>NUL&EXIT)

REM 设置安装名称：
set "menuRoot=VSCode"
REM 设置安装路径：
set "menuPath=D:\Peng\App\DevApp\Microsoft VS Code\Code.exe"
REM 设置菜单名称：
set "menuName=通过 Code 打开"

:MENU
ECHO.&ECHO 1、添加系统右键 %menuRoot% 打开项
ECHO.&ECHO 2、移除系统右键 %menuRoot% 打开项
IF EXIST "%WinDir%\System32\CHOICE.exe" CHOICE /C 12 /N >NUL 2>NUL
IF EXIST "%WinDir%\System32\CHOICE.exe" IF "%ERRORLEVEL%"=="2" GOTO RemoveMenu
IF EXIST "%WinDir%\System32\CHOICE.exe" IF "%ERRORLEVEL%"=="1" GOTO AddMenu
IF NOT EXIST "%WinDir%\System32\CHOICE.exe" ECHO.&SET /p choice=输入数字项敲回车键：
IF NOT EXIST "%WinDir%\System32\CHOICE.exe" IF NOT "%choice%"=="" SET choice=%choice:~0,1%
IF NOT EXIST "%WinDir%\System32\CHOICE.exe" IF /I "%choice%"=="1" GOTO AddMenu
IF NOT EXIST "%WinDir%\System32\CHOICE.exe" IF /I "%choice%"=="2" GOTO RemoveMenu
IF NOT EXIST "%WinDir%\System32\CHOICE.exe" ECHO.&ECHO 输入无效 &PAUSE&CLS&GOTO MENU

:AddMenu
reg add "HKEY_CLASSES_ROOT\Directory\shell\%menuRoot%" /ve /d "%menuName%" /f
reg add "HKEY_CLASSES_ROOT\Directory\shell\%menuRoot%" /v "Icon" /d "\"%menuPath%\"" /f
reg add "HKEY_CLASSES_ROOT\Directory\shell\%menuRoot%\command" /ve /d "\"%menuPath%\" \"%%V\"" /f
IF EXIST "%WinDir%\System32\CHOICE.exe" ( 
	ECHO.&ECHO 添加完成
	TIMEOUT /t 2 >NUL & CLS & GOTO MENU
) ELSE ( 
	ECHO.&ECHO 已添加，任意键返回 &PAUSE>NUL&CLS&GOTO MENU
) 

:RemoveMenu
reg delete "HKEY_CLASSES_ROOT\Directory\shell\%menuRoot%" /f >NUL 2>NUL
IF EXIST "%WinDir%\System32\CHOICE.exe" ( 
	ECHO.&ECHO 移除完成
	TIMEOUT /t 2 >NUL & CLS & GOTO MENU
) ELSE ( 
	ECHO.&ECHO 已删除，任意键返回 &PAUSE>NUL&CLS&GOTO MENU
) 