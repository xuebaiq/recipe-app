@echo off
chcp 65001 >nul
echo ====================================
echo    菜谱推荐系统启动脚本
echo ====================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 检测Python环境... OK
echo.

REM 进入后端目录
cd /d "%~dp0backend"

REM 检查是否已安装依赖
if not exist "venv\" (
    echo [2/4] 首次运行，正在创建虚拟环境...
    python -m venv venv
    echo.
    echo [3/4] 正在安装依赖包...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
) else (
    echo [2/4] 虚拟环境已存在... OK
    echo [3/4] 依赖包已安装... OK
    echo.
    call venv\Scripts\activate.bat
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
echo ====================================
echo.
echo 按 Ctrl+C 停止服务器
echo.

REM 启动Flask应用
python app.py

pause
