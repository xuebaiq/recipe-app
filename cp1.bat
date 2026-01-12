@echo off
:: 设置编码为UTF-8，防止乱码
chcp 65001 >nul
title 菜谱程序启动器

:: 1. 进入后端目录
cd /d "%~dp0backend"

:: 2. 尝试激活环境 (如果环境不存在，会报错并提示)
echo [正在启动] 正在激活 Conda 环境...
call conda activate recipe-env || (
    echo [错误] 找不到 recipe-env 环境，请先确认环境已创建。
    pause
    exit /b
)

:: 3. 检查 API Key 并启动
if not defined SILICONFLOW_API_KEY (
    echo [提示] 当前为本地模式 (未设置 API Key)
)

echo [成功] 服务器即将在 http://localhost:5000 运行
echo 按 Ctrl+C 退出程序
python app.py

pause