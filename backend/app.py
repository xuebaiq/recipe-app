# -*- coding: utf-8 -*-
"""
菜谱推荐系统 - Flask后端
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import random
import requests
from lunar_python import Lunar, Solar

# 配置Flask指向frontend目录
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
app = Flask(__name__,
            static_folder=os.path.join(frontend_dir, 'static'),
            template_folder=frontend_dir)
CORS(app)  # 允许跨域请求

# 加载菜谱数据
def load_recipes():
    """加载菜谱数据"""
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'recipes.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

RECIPES = load_recipes()

# 节日菜谱映射
FESTIVAL_FOODS = {
    "春节": ["饺子", "年糕", "鱼"],
    "元宵节": ["元宵", "汤圆"],
    "清明节": ["青团"],
    "端午节": ["粽子"],
    "中秋节": ["月饼"],
    "冬至": ["饺子", "汤圆"],
    "腊八节": ["八宝粥"],
    "除夕": ["饺子", "年夜饭"]
}

# 时令蔬菜推荐
SEASONAL_INGREDIENTS = {
    "春季": ["韭菜", "菠菜", "春笋", "荠菜", "豌豆"],
    "夏季": ["黄瓜", "番茄", "茄子", "豆角", "空心菜"],
    "秋季": ["南瓜", "红薯", "莲藕", "芋头", "白菜"],
    "冬季": ["白菜", "萝卜", "土豆", "山药", "菠菜"]
}

def get_lunar_info():
    """获取农历信息"""
    today = datetime.now()
    solar = Solar.fromDate(today)
    lunar = Lunar.fromSolar(solar)

    return {
        "lunar_date": f"{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}",
        "festival": lunar.getFestivals() + lunar.getOtherFestivals(),
        "solar_term": lunar.getJieQi(),
        "year": lunar.getYearInGanZhi(),
        "month": lunar.getMonth(),
        "day": lunar.getDay()
    }

def get_season():
    """根据农历获取季节"""
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "春季"
    elif month in [6, 7, 8]:
        return "夏季"
    elif month in [9, 10, 11]:
        return "秋季"
    else:
        return "冬季"

def recommend_recipes(diet_type="中餐", meal_time="午餐"):
    """
    推荐菜谱
    :param diet_type: 饮食类型（中餐/地中海）
    :param meal_time: 餐次（早餐/午餐/晚餐）
    :return: 推荐的菜谱列表
    """
    lunar_info = get_lunar_info()
    season = get_season()

    # 筛选符合条件的菜谱
    filtered = [r for r in RECIPES
                if r['category'] == diet_type
                and meal_time in r['meal_type']]

    # 优先推荐节日菜
    festival_recipes = []
    if lunar_info['festival']:
        for festival in lunar_info['festival']:
            festival_recipes = [r for r in filtered if r.get('festival') and festival in r.get('festival', '')]

    # 推荐时令菜
    seasonal_recipes = [r for r in filtered if season in r.get('season', '全年')]

    # 根据BMI推荐低热量菜（BMI=34属于肥胖）
    low_cal_recipes = [r for r in filtered if r['calories'] in ['低', '中']]

    # 组合推荐
    recommended = []

    # 1. 节日菜优先
    if festival_recipes:
        recommended.extend(festival_recipes[:2])

    # 2. 时令菜
    remaining = 7 if diet_type == "中餐" else 4
    seasonal_pool = [r for r in seasonal_recipes if r not in recommended]
    random.shuffle(seasonal_pool)
    recommended.extend(seasonal_pool[:remaining - len(recommended)])

    # 3. 补充健康低卡菜
    if len(recommended) < remaining:
        low_cal_pool = [r for r in low_cal_recipes if r not in recommended]
        random.shuffle(low_cal_pool)
        recommended.extend(low_cal_pool[:remaining - len(recommended)])

    # 4. 如果还不够，随机补充
    if len(recommended) < remaining:
        other_pool = [r for r in filtered if r not in recommended]
        random.shuffle(other_pool)
        recommended.extend(other_pool[:remaining - len(recommended)])

    return recommended[:remaining]

def call_deepseek_api(prompt):
    """
    调用硅基流动的DeepSeek API
    :param prompt: 提示词
    :return: API返回的文本
    """
    api_key = os.environ.get('SILICONFLOW_API_KEY')

    if not api_key:
        return None

    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [
            {
                "role": "system",
                "content": "你是一位专业的中餐和地中海饮食营养师，擅长制定健康菜谱。回答要简洁实用，适合给老人使用。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"API调用失败: {e}")
        return None

def search_in_database(keyword, recipe_type="菜名"):
    """
    在本地数据库中搜索
    :param keyword: 关键词（蔬菜名或菜名）
    :param recipe_type: 搜索类型（蔬菜/菜名）
    :return: 匹配的菜谱
    """
    results = []

    if recipe_type == "蔬菜":
        # 搜索食材中包含该蔬菜的菜谱
        for recipe in RECIPES:
            if any(keyword in ingredient for ingredient in recipe['ingredients']):
                results.append(recipe)
    else:
        # 搜索菜名
        for recipe in RECIPES:
            if keyword in recipe['name']:
                results.append(recipe)

    return results

def search_recipe(keyword, search_type="auto"):
    """
    搜索菜谱（本地优先，不足时调用API）
    :param keyword: 关键词
    :param search_type: 搜索类型（auto/菜名/蔬菜）
    :return: 搜索结果
    """
    # 判断是蔬菜还是菜名
    if search_type == "auto":
        # 检查是否在常见蔬菜列表中
        common_veggies = set()
        for veggies in SEASONAL_INGREDIENTS.values():
            common_veggies.update(veggies)

        if keyword in common_veggies or len(keyword) <= 3:
            search_type = "蔬菜"
        else:
            search_type = "菜名"

    # 从本地数据库搜索
    local_results = search_in_database(keyword, search_type)

    # 判断是否需要API补充
    required_count = 6 if search_type == "蔬菜" else 2

    if len(local_results) >= required_count:
        return {
            "keyword": keyword,
            "type": search_type,
            "source": "本地数据库",
            "results": local_results[:required_count]
        }

    # 本地不足，调用API
    api_result = None
    if search_type == "蔬菜":
        prompt = f"请给出{keyword}的6种不同做法，每种做法包括：菜名、所需食材（详细列表）、简要步骤（5步以内）。以JSON格式返回。"
    else:
        prompt = f"请给出'{keyword}'这道菜的2种常见不同做法，每种包括：做法名称、所需食材（详细列表）、详细步骤。以JSON格式返回。"

    api_response = call_deepseek_api(prompt)

    return {
        "keyword": keyword,
        "type": search_type,
        "source": "本地数据库" if len(local_results) >= required_count else "本地+API",
        "local_results": local_results,
        "api_response": api_response,
        "results": local_results[:required_count]
    }

# ============== API路由 ==============

@app.route('/api/today', methods=['GET'])
def get_today_recommendations():
    """获取今日推荐菜谱"""
    diet_type = request.args.get('diet_type', '中餐')  # 中餐/地中海

    lunar_info = get_lunar_info()
    season = get_season()

    # 获取三餐推荐
    breakfast = recommend_recipes(diet_type, "早餐")
    lunch = recommend_recipes(diet_type, "午餐")
    dinner = recommend_recipes(diet_type, "晚餐")

    return jsonify({
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "lunar": lunar_info,
        "season": season,
        "diet_type": diet_type,
        "recommendations": {
            "breakfast": breakfast,
            "lunch": lunch,
            "dinner": dinner
        }
    })

@app.route('/api/search', methods=['POST'])
def search():
    """搜索菜谱"""
    data = request.json
    keyword = data.get('keyword', '')
    search_type = data.get('type', 'auto')

    if not keyword:
        return jsonify({"error": "请输入搜索关键词"}), 400

    result = search_recipe(keyword, search_type)
    return jsonify(result)

@app.route('/api/recipes', methods=['GET'])
def get_all_recipes():
    """获取所有菜谱（分页）"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    category = request.args.get('category', '')  # 中餐/地中海

    filtered = RECIPES
    if category:
        filtered = [r for r in RECIPES if r['category'] == category]

    start = (page - 1) * per_page
    end = start + per_page

    return jsonify({
        "total": len(filtered),
        "page": page,
        "per_page": per_page,
        "recipes": filtered[start:end]
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "total_recipes": len(RECIPES),
        "chinese_recipes": len([r for r in RECIPES if r['category'] == '中餐']),
        "mediterranean_recipes": len([r for r in RECIPES if r['category'] == '地中海'])
    })

@app.route('/')
def index():
    """首页 - 返回前端页面"""
    return send_from_directory(app.template_folder, 'index.html')

if __name__ == '__main__':
    print("=" * 50)
    print("菜谱推荐系统启动中...")
    print(f"共加载 {len(RECIPES)} 道菜谱")
    print(f"中餐: {len([r for r in RECIPES if r['category'] == '中餐'])} 道")
    print(f"地中海: {len([r for r in RECIPES if r['category'] == '地中海'])} 道")
    print("=" * 50)
    # 从环境变量读取端口号（用于云平台部署）
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
