// 全局变量
const API_BASE_URL = '/api';
//const API_BASE_URL = 'http://localhost:5000/api';
let currentDietType = '中餐'; // 当前饮食类型
let currentData = null; // 当前推荐数据
let currentSearchKeyword = ''; // 当前搜索关键词
let currentSearchPage = 1; // 当前搜索页码
let currentSearchData = null; // 当前搜索完整数据

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initApp();
    bindEvents();
});

// 初始化应用
function initApp() {
    updateDate();
    loadTodayRecommendations();
}

// 绑定事件
function bindEvents() {
    // 饮食切换按钮
    document.getElementById('diet-toggle').addEventListener('click', toggleDietType);

    // 刷新按钮
    document.getElementById('refresh-btn').addEventListener('click', loadTodayRecommendations);

    // 搜索按钮
    document.getElementById('search-btn').addEventListener('click', performSearch);

    // 搜索输入框回车
    document.getElementById('search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // 返回按钮
    document.getElementById('back-btn').addEventListener('click', showRecommendations);

    // 弹窗关闭
    document.querySelector('.close').addEventListener('click', closeModal);
    window.addEventListener('click', function(e) {
        const modal = document.getElementById('recipe-modal');
        if (e.target === modal) {
            closeModal();
        }
    });
}

// 更新日期显示 - v3.0 带星期和emoji
function updateDate() {
    const now = new Date();
    const dateStr = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`;
    const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
    const weekDay = weekDays[now.getDay()];
    document.getElementById('current-date').textContent = `📅 ${dateStr} ${weekDay}`;
}

// 切换饮食类型 - v3.0 带emoji图标切换
function toggleDietType() {
    const btn = document.getElementById('diet-toggle');

    if (currentDietType === '中餐') {
        currentDietType = '地中海';
        btn.innerHTML = '🥗 <span id="diet-text">地中海饮食</span>';
        btn.classList.add('mediterranean');
    } else {
        currentDietType = '中餐';
        btn.innerHTML = '🍜 <span id="diet-text">中餐</span>';
        btn.classList.remove('mediterranean');
    }

    loadTodayRecommendations();
}

// 加载今日推荐
async function loadTodayRecommendations() {
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/today?diet_type=${encodeURIComponent(currentDietType)}`);
        const data = await response.json();

        currentData = data;
        displayRecommendations(data);
    } catch (error) {
        console.error('加载推荐失败:', error);
        showError('无法加载推荐，请检查网络连接或稍后重试');
    }
}

// 显示加载状态
function showLoading() {
    const grids = ['breakfast-grid', 'lunch-grid', 'dinner-grid'];
    grids.forEach(gridId => {
        const grid = document.getElementById(gridId);
        grid.innerHTML = '<div class="loading">精心挑选中...</div>';
    });
}

// 显示错误
function showError(message) {
    const grids = ['breakfast-grid', 'lunch-grid', 'dinner-grid'];
    grids.forEach(gridId => {
        const grid = document.getElementById(gridId);
        grid.innerHTML = `<div class="loading" style="color: #f44336;">${message}</div>`;
    });
}

// 显示推荐菜谱 - v3.0 带灯笼emoji
function displayRecommendations(data) {
    // 更新农历信息
    if (data.lunar) {
        document.getElementById('lunar-date').textContent = `🏮 农历 ${data.lunar.lunar_date}`;

        // 显示节日提示
        if (data.lunar.festival && data.lunar.festival.length > 0) {
            const festivalNotice = document.getElementById('festival-notice');
            const festivalText = document.getElementById('festival-text');
            festivalText.textContent = `${data.lunar.festival[0]} - 为您推荐节日美食`;
            festivalNotice.style.display = 'block';
        } else {
            document.getElementById('festival-notice').style.display = 'none';
        }
    }

    // 显示早餐
    renderRecipeGrid('breakfast-grid', data.recommendations.breakfast);

    // 显示午餐
    renderRecipeGrid('lunch-grid', data.recommendations.lunch);

    // 显示晚餐
    renderRecipeGrid('dinner-grid', data.recommendations.dinner);
}

// 渲染菜谱网格
function renderRecipeGrid(gridId, recipes) {
    const grid = document.getElementById(gridId);

    if (!recipes || recipes.length === 0) {
        grid.innerHTML = '<div class="loading">暂无推荐</div>';
        return;
    }

    grid.innerHTML = recipes.map(recipe => createRecipeCard(recipe)).join('');

    // 绑定点击事件
    grid.querySelectorAll('.recipe-card').forEach((card, index) => {
        card.addEventListener('click', () => showRecipeDetail(recipes[index]));
    });
}

// 创建菜谱卡片
function createRecipeCard(recipe) {
    const caloriesClass = recipe.calories === '低' ? 'calories-low' :
                         recipe.calories === '中' ? 'calories-medium' : 'calories-high';

    const tags = recipe.tags ? recipe.tags.slice(0, 2).map(tag =>
        `<span class="tag">${tag}</span>`
    ).join('') : '';

    const ingredients = recipe.ingredients.slice(0, 3).join('、');

    return `
        <div class="recipe-card">
            <h3>${recipe.name}</h3>
            <div class="recipe-tags">
                <span class="tag ${caloriesClass}">${recipe.calories}热量</span>
                ${tags}
            </div>
            <div class="ingredients-preview">
                📋 ${ingredients}...
            </div>
        </div>
    `;
}

// 显示菜谱详情弹窗
function showRecipeDetail(recipe) {
    const modal = document.getElementById('recipe-modal');
    const modalName = document.getElementById('modal-recipe-name');
    const modalCalories = document.getElementById('modal-calories');
    const modalSeason = document.getElementById('modal-season');
    const modalIngredients = document.getElementById('modal-ingredients');
    const modalSteps = document.getElementById('modal-steps');

    // 设置内容
    modalName.textContent = recipe.name;

    const caloriesClass = recipe.calories === '低' ? 'calories-low' :
                         recipe.calories === '中' ? 'calories-medium' : 'calories-high';
    modalCalories.className = `tag ${caloriesClass}`;
    modalCalories.textContent = `${recipe.calories}热量`;

    modalSeason.textContent = recipe.season;

    // 食材列表
    modalIngredients.innerHTML = recipe.ingredients.map(ing => `<li>${ing}</li>`).join('');

    // 步骤列表
    modalSteps.innerHTML = recipe.steps.map(step => `<li>${step}</li>`).join('');

    // 显示弹窗
    modal.style.display = 'block';
}

// 关闭弹窗
function closeModal() {
    document.getElementById('recipe-modal').style.display = 'none';
}

// 执行搜索
async function performSearch() {
    const keyword = document.getElementById('search-input').value.trim();

    if (!keyword) {
        alert('请输入搜索关键词');
        return;
    }

    // 重置搜索状态
    currentSearchKeyword = keyword;
    currentSearchPage = 1;

    // 显示搜索结果区域
    showSearchResults();

    const searchGrid = document.getElementById('search-grid');
    searchGrid.innerHTML = '<div class="loading">搜索中...</div>';

    await loadSearchResults();
}

// 加载搜索结果
async function loadSearchResults(append = false) {
    const searchGrid = document.getElementById('search-grid');

    try {
        const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                keyword: currentSearchKeyword,
                type: 'auto',
                page: currentSearchPage,
                page_size: 3  // 每次加载3个
            })
        });

        const data = await response.json();
        currentSearchData = data;
        displaySearchResults(data, append);
    } catch (error) {
        console.error('搜索失败:', error);
        searchGrid.innerHTML = '<div class="loading" style="color: #f44336;">搜索失败，请重试</div>';
    }
}

// 加载更多结果
async function loadMoreResults() {
    currentSearchPage++;

    const loadMoreBtn = document.getElementById('load-more-btn');
    loadMoreBtn.textContent = '加载中...';
    loadMoreBtn.disabled = true;

    await loadSearchResults(true);
}

// 显示搜索结果
function displaySearchResults(data, append = false) {
    const searchTitle = document.getElementById('search-title');
    const searchGrid = document.getElementById('search-grid');

    // 第一页时设置标题
    if (!append) {
        const typeText = data.type === '蔬菜' ? '的做法' : '的不同做法';
        const totalInfo = data.pagination ? ` (共找到${data.pagination.total_count}个结果)` : '';
        searchTitle.textContent = `"${data.keyword}"${typeText}${totalInfo}`;
    }

    // 显示结果
    if (!data.results || data.results.length === 0) {
        if (append) return; // 追加模式下没有结果就直接返回

        // 判断是否有API响应（包括超时信息）
        const hasApiInfo = data.api_response && data.api_response.trim() !== '';
        const isTimeout = hasApiInfo && data.api_response.includes('超时');

        searchGrid.innerHTML = `
            <div class="recipe-detail-card">
                <h3>未找到相关菜谱</h3>
                <p style="font-size: 18px; color: #666; margin-top: 10px;">
                    本地数据库中暂无"${data.keyword}"的菜谱。
                </p>
                ${hasApiInfo ? `
                    <div style="margin-top: 20px; padding: 15px; background: ${isTimeout ? '#fff3cd' : '#f0f8ff'}; border-radius: 8px; border-left: 4px solid ${isTimeout ? '#ffc107' : '#4CAF50'};">
                        <p style="font-size: 17px; line-height: 1.8; white-space: pre-wrap; margin: 0;">
                            ${isTimeout ? '⚠️ ' : '💡 '}${data.api_response}
                        </p>
                    </div>
                ` : '<p style="margin-top: 10px; color: #999;">请尝试其他关键词。</p>'}
            </div>
        `;
        return;
    }

    // 渲染结果卡片
    const resultsHTML = data.results.map(recipe => `
        <div class="recipe-detail-card">
            <h3>${recipe.name}</h3>
            <div class="recipe-tags">
                <span class="tag ${recipe.calories === '低' ? 'calories-low' : recipe.calories === '中' ? 'calories-medium' : 'calories-high'}">
                    ${recipe.calories}热量
                </span>
                ${recipe.tags ? recipe.tags.map(tag => `<span class="tag">${tag}</span>`).join('') : ''}
            </div>

            <h4>📋 所需食材</h4>
            <ul>
                ${recipe.ingredients.map(ing => `<li>${ing}</li>`).join('')}
            </ul>

            <h4>👨‍🍳 制作步骤</h4>
            <ol>
                ${recipe.steps.map(step => `<li>${step}</li>`).join('')}
            </ol>
        </div>
    `).join('');

    if (append) {
        // 追加模式：移除旧的加载更多按钮，添加新结果
        const oldBtn = document.getElementById('load-more-btn');
        if (oldBtn) oldBtn.remove();
        searchGrid.insertAdjacentHTML('beforeend', resultsHTML);
    } else {
        // 新搜索：替换内容
        searchGrid.innerHTML = resultsHTML;
    }

    // 如果有更多结果，显示"加载更多"按钮
    if (data.pagination && data.pagination.has_more) {
        const loadMoreHTML = `
            <div style="text-align: center; margin: 30px 0;">
                <button id="load-more-btn" class="btn" style="padding: 12px 40px; font-size: 16px;">
                    加载更多 (还有${data.pagination.total_count - data.pagination.current_page * data.pagination.page_size}个结果)
                </button>
            </div>
        `;
        searchGrid.insertAdjacentHTML('beforeend', loadMoreHTML);

        // 绑定加载更多按钮事件
        document.getElementById('load-more-btn').addEventListener('click', loadMoreResults);
    }

    // 如果有API响应且是第一页，追加显示
    if (!append && data.api_response && data.api_response.trim() !== '') {
        const hasApiInfo = data.api_response && data.api_response.trim() !== '';
        const isTimeout = hasApiInfo && data.api_response.includes('超时');

        searchGrid.insertAdjacentHTML('beforeend', `
            <div class="recipe-detail-card" style="background: ${isTimeout ? '#fff3cd' : '#f0f8ff'};">
                <h3>${isTimeout ? '⚠️ 提示' : '💡 AI推荐的更多做法'}</h3>
                <div style="font-size: 17px; line-height: 1.8; white-space: pre-wrap;">
                    ${data.api_response}
                </div>
            </div>
        `);
    }
}

// 显示搜索结果区域
function showSearchResults() {
    document.getElementById('recommendations').style.display = 'none';
    document.getElementById('search-results').style.display = 'block';
}

// 显示推荐区域
function showRecommendations() {
    document.getElementById('recommendations').style.display = 'block';
    document.getElementById('search-results').style.display = 'none';
    document.getElementById('search-input').value = '';
}

// 工具函数：格式化日期
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// v3.0 更新完成
console.log('菜谱推荐系统 v3.0 已加载');
