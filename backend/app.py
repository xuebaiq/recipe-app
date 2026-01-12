# -*- coding: utf-8 -*-
import os
import json
import random
import requests
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from lunar_python import Lunar, Solar

# --- 1. 路径自动适配逻辑 ---
# 获取当前 app.py 所在的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 自动定位前端文件夹 (假设结构是 recipe-app/backend/app.py 和 recipe-app/frontend/)
PARENT_DIR = os.path.dirname(BASE_DIR)
frontend_dir = os.path.join(PARENT_DIR, 'frontend')

app = Flask(__name__,
            static_folder=os.path.join(frontend_dir, 'static'),
            template_folder=frontend_dir)
CORS(app)  # 开启跨域，确保手机能连上

# --- 2. 数据库加载逻辑 (多路径兼容) ---
def load_recipes():
    """多路径尝试加载 recipes.json"""
    paths_to_try = [
        os.path.join(BASE_DIR, 'recipes.json'),
        os.path.join(BASE_DIR, 'data', 'recipes.json'),
        os.path.join(PARENT_DIR, 'recipes.json')
    ]
    for path in paths_to_try:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"读取 {path} 出错: {e}")
    return []

RECIPES = load_recipes()

# --- 3. 农历与季节逻辑 ---
def get_lunar_info():
    """获取农历信息，增加完善的错误保护"""
    try:
        today = datetime.now()
        solar = Solar.fromDate(today)
        lunar = Lunar.fromSolar(solar)
        
        # 处理节日列表，防止返回 None 导致合并报错
        festivals = lunar.getFestivals() or []
        other_festivals = lunar.getOtherFestivals() or []
        
        return {
            "lunar_date": f"{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}",
            "festival": festivals + other_festivals,
            "solar_term": lunar.getJieQi() or "",
            "year": lunar.getYearInGanZhi(),
            "month": lunar.getMonth(),
            "day": lunar.getDay()
        }
    except Exception as e:
        print(f"农历转换出错: {e}")
        return {"lunar_date": "加载中", "festival": [], "solar_term": ""}

def get_season():
    month = datetime.now().month
    if month in [3, 4, 5]: return "春季"
    elif month in [6, 7, 8]: return "夏季"
    elif month in [9, 10, 11]: return "秋季"
    else: return "冬季"

# --- 4. 推荐核心逻辑 ---
def recommend_recipes(diet_type="中餐", meal_time="午餐"):
    lunar_info = get_lunar_info()
    season = get_season()
    
    # 基础筛选
    filtered = [r for r in RECIPES if r.get('category') == diet_type and meal_time in r.get('meal_type', [])]
    if not filtered: return []

    recommended = []
    # 节日优先
    if lunar_info['festival']:
        for f in lunar_info['festival']:
            recommended.extend([r for r in filtered if r.get('festival') and f in r.get('festival')])

    # 时令优先
    seasonal_pool = [r for r in filtered if season in r.get('season', '全年') and r not in recommended]
    random.shuffle(seasonal_pool)
    
    # 设定推荐数量
    limit = 7 if diet_type == "中餐" else 4
    recommended.extend(seasonal_pool[:limit - len(recommended)])

    # 兜底：如果还没够，随机补齐
    if len(recommended) < limit:
        others = [r for r in filtered if r not in recommended]
        random.shuffle(others)
        recommended.extend(others[:limit - len(recommended)])

    return recommended[:limit]

# --- 5. API 路由 ---
@app.route('/api/today', methods=['GET'])
def get_today_recommendations():
    diet_type = request.args.get('diet_type', '中餐')
    return jsonify({
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "lunar": get_lunar_info(),
        "season": get_season(),
        "recommendations": {
            "breakfast": recommend_recipes(diet_type, "早餐"),
            "lunch": recommend_recipes(diet_type, "午餐"),
            "dinner": recommend_recipes(diet_type, "晚餐")
        }
    })

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "db_size": len(RECIPES)})

@app.route('/')
def index():
    # 优先返回 frontend 目录下的 index.html
    return send_from_directory(app.template_folder, 'index.html')

if __name__ == '__main__':
    # 兼容云端端口
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)