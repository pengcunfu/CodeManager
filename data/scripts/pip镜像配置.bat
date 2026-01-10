@echo off
echo ===========================================
echo 请选择要设置的 PIP 源：
echo 1. 豆瓣源
echo 2. 官方源
echo 3. 华为源
echo 4. 清华源
echo 5. 阿里源
echo ===========================================
set /p choice=请输入对应的数字 (1-5): 

if "%choice%"=="1" (
    echo 配置豆瓣源...
    python -m pip config set global.index-url http://pypi.douban.com/simple/
    python -m pip config set install.trusted-host pypi.douban.com
    goto done
)

if "%choice%"=="2" (
    echo 配置官方源...
    python -m pip config set global.index-url https://pypi.python.org/simple
    python -m pip config set install.trusted-host pypi.python.org
    goto done
)

if "%choice%"=="3" (
    echo 配置华为源...
    python -m pip config set global.index-url https://repo.huaweicloud.com/repository/pypi/simple
    python -m pip config set global.trusted-host repo.huaweicloud.com
    python -m pip config set global.timeout 120
    goto done
)

if "%choice%"=="4" (
    echo 配置清华源...
    python -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
    python -m pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn
    goto done
)

if "%choice%"=="5" (
    echo 配置阿里源...
    python -m pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    python -m pip config set global.trusted-host mirrors.aliyun.com
    goto done
)

echo 输入错误，请重新运行脚本！
goto end

:done
echo 配置已完成！
pause
:end