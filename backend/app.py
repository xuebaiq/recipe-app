# -*- coding: utf-8 -*-
import os
import json
import random
import requests
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from lunar_python import Lunar, Solar
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

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

@app.route('/api/search', methods=['POST'])
def search_recipes():
    """搜索菜谱"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()

        if not keyword:
            return jsonify({"error": "请输入搜索关键词"}), 400

        # 判断搜索类型（蔬菜或菜名）
        vegetables = ['白菜', '萝卜', '土豆', '西红柿', '番茄', '黄瓜', '茄子', '豆角', '青椒', '辣椒',
                     '芹菜', '菠菜', '韭菜', '香菜', '生菜', '油菜', '空心菜', '西兰花', '花菜',
                     '胡萝卜', '洋葱', '大蒜', '生姜', '南瓜', '冬瓜', '丝瓜', '苦瓜', '豆芽',
                     '莴笋', '芦笋', '蘑菇', '木耳', '香菇', '金针菇', '平菇', '豆腐', '竹笋']

        search_type = '蔬菜' if any(veg in keyword for veg in vegetables) else '菜名'

        # 获取分页参数
        page = int(data.get('page', 1))  # 当前页码，默认第1页
        page_size = int(data.get('page_size', 3))  # 每页显示数量，默认3个

        # 本地搜索 - 搜索所有匹配结果
        all_results = []
        for recipe in RECIPES:
            # 在菜名、食材中搜索
            if (keyword in recipe.get('name', '') or
                any(keyword in ing for ing in recipe.get('ingredients', []))):
                all_results.append(recipe)

        # 计算分页
        total_count = len(all_results)
        total_pages = (total_count + page_size - 1) // page_size  # 向上取整
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        results = all_results[start_idx:end_idx]

        # 只在第一页且结果不够时调用API
        api_response = None
        if page == 1 and total_count < page_size:
            api_response = call_siliconflow_api(keyword, search_type)

        return jsonify({
            "keyword": keyword,
            "type": search_type,
            "source": "本地数据库" if all_results else "AI推荐",
            "results": results,
            "api_response": api_response,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_more": page < total_pages
            }
        })

    except Exception as e:
        print(f"搜索出错: {e}")
        return jsonify({"error": "搜索失败，请稍后重试"}), 500

def call_siliconflow_api(keyword, search_type):
    """调用硅基流动API获取菜谱推荐"""
    api_key = os.environ.get('SILICONFLOW_API_KEY', '')

    if not api_key:
        return None

    try:
        url = "https://api.siliconflow.cn/v1/chat/completions"

        # 构建提示词
        if search_type == '蔬菜':
            prompt = f"请推荐3-4道以{keyword}为主料的家常菜，每道菜包含：菜名、食材清单、制作步骤。要求简洁实用，适合家庭制作。"
        else:
            prompt = f"请提供{keyword}的详细做法，包含：食材清单、制作步骤。要求步骤清晰，适合家庭制作。"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-ai/DeepSeek-V3",
            "messages": [
                {"role": "system", "content": "你是一个专业的中餐厨师，擅长制作家常菜。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"API调用失败: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print(f"API调用超时: 请求超过30秒")
        return "AI服务响应超时，请稍后再试。您可以尝试搜索其他菜谱。"
    except requests.exceptions.RequestException as e:
        print(f"API网络错误: {e}")
        return None
    except Exception as e:
        print(f"API调用出错: {e}")
        return None

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