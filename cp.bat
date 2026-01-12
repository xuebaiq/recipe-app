@echo off
chcp 65001 >nul
echo ====================================
echo    菜谱推荐系统启动脚本
echo    (Anaconda版本)
echo ====================================
echo.

REM 检查conda是否可用
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Anaconda/Miniconda
    echo 请确保已安装Anaconda并初始化到命令行
    echo 或者运行 Anaconda Prompt 后再执行此脚本
    pause
    exit /b 1
)

echo [1/4] 检测Conda环境... OK
echo.

REM 进入后端目录
cd /d "%~dp0backend"

REM 检查recipe-env环境是否存在
conda env list | findstr "recipe-env" >nul 2>&1
if %errorlevel% neq 0 (
    echo [2/4] 首次运行，正在创建Conda环境 recipe-env...
    conda create -n recipe-env python=3.10 -y
    echo.
    echo [3/4] 正在安装依赖包...
    call conda activate recipe-env
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
) else (
    echo [2/4] Conda环境 recipe-env 已存在... OK
    echo [3/4] 激活环境并检查依赖...
    call conda activate recipe-env
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
    echo.
)

REM 检查API Key（可选）
if not defined SILICONFLOW_API_KEY (
    echo [提示] 未设置API Key，将仅使用本地数据库
    echo [提示] 如需使用AI扩展功能，请设置环境变量 SILICONFLOW_API_KEY
    echo.
)

echo [4/4] 正在启动服务器...
echo.
echo ====================================
echo   服务器启动成功！
echo   请在浏览器中打开：
echo   http://localhost:5000
echo.
echo   Conda环境: recipe-env
echo ====================================
echo.
echo 按 Ctrl+C 停止服务器
echo.

REM 启动Flask应用
python app.py

pause
