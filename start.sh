#!/bin/bash

echo "===================================="
echo "   菜谱推荐系统启动脚本"
echo "===================================="
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "[1/4] 检测Python环境... OK"
echo ""

# 进入后端目录
cd "$(dirname "$0")/backend"

# 检查是否已安装依赖
if [ ! -d "venv" ]; then
    echo "[2/4] 首次运行，正在创建虚拟环境..."
    python3 -m venv venv
    echo ""
    echo "[3/4] 正在安装依赖包..."
    source venv/bin/activate
    pip install -r requirements.txt
    echo ""
else
    echo "[2/4] 虚拟环境已存在... OK"
    echo "[3/4] 依赖包已安装... OK"
    echo ""
    source venv/bin/activate
fi

# 检查API Key（可选）
if [ -z "$SILICONFLOW_API_KEY" ]; then
    echo "[提示] 未设置API Key，将仅使用本地数据库"
    echo "[提示] 如需使用AI扩展功能，请设置环境变量 SILICONFLOW_API_KEY"
    echo ""
fi

echo "[4/4] 正在启动服务器..."
echo ""
echo "===================================="
echo "  服务器启动成功！"
echo "  请在浏览器中打开："
echo "  http://localhost:5000"
echo "===================================="
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动Flask应用
python app.py
