@echo off
title Python Library Installer
:menu
echo ==========================================
echo Python Library Installer
echo ==========================================
echo 1. 安装网络爬虫相关库
echo 2. 安装数据分析相关库
echo 3. 安装机器学习相关库
echo 4. 安装文本处理相关库
echo 5. 安装对象存储相关库
echo 6. 安装数据库相关库
echo 7. 安装桌面开发相关库 (PyQt)
echo 8. 安装所有库
echo 0. 退出
echo ==========================================
set /p choice=请选择一个选项（0-8）：

if "%choice%"=="1" goto install_spider
if "%choice%"=="2" goto install_data_analysis
if "%choice%"=="3" goto install_machine_learning
if "%choice%"=="4" goto install_text_processing
if "%choice%"=="5" goto install_object_storage
if "%choice%"=="6" goto install_database
if "%choice%"=="7" goto install_desktop
if "%choice%"=="8" goto install_all
if "%choice%"=="0" goto exit
goto invalid_choice

:install_spider
echo 正在安装网络爬虫相关库...
python -m pip install requests beautifulsoup4 scrapy selenium
goto end

:install_data_analysis
echo 正在安装数据分析相关库...
python -m pip install pandas numpy matplotlib seaborn scipy
goto end

:install_machine_learning
echo 正在安装机器学习相关库...
python -m pip install scikit-learn tensorflow keras xgboost
goto end

:install_text_processing
echo 正在安装文本处理相关库...
python -m pip install nltk spacy textblob jieba
goto end

:install_object_storage
echo 正在安装对象存储相关库...
python -m pip install oss2 boto3 minio
goto end

:install_database
echo 正在安装数据库相关库...
python -m pip install psycopg2 mysql-connector-python sqlalchemy pymongo redis
goto end

:install_desktop
echo 正在安装桌面开发相关库 (PyQt)...
python -m pip install PyQt5 PyQt6 pyqtgraph
goto end

:install_all
echo 正在安装所有分类的库...
call :install_spider
call :install_data_analysis
call :install_machine_learning
call :install_text_processing
call :install_object_storage
call :install_database
call :install_desktop
goto end

:invalid_choice
echo 无效选择，请重新输入。
goto menu

:end
echo 安装完成！按任意键退出...
pause
exit

:exit
echo 程序已退出。按任意键关闭...
pause
exit