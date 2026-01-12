# 🆓 Render 部署教程（完全免费）

## ✅ 为什么选Render？

- 💰 **永久免费**（不是试用期）
- 🚀 **5分钟部署完成**
- 🔒 **自动SSL证书**（https）
- 🌐 **可绑定自定义域名**
- ☁️ **自动从GitHub部署**

## ⚠️ 免费套餐的限制

- 15分钟无访问会休眠
- 首次唤醒需要30秒
- **但是**：给妈妈用，每天都会访问，基本不会休眠！

---

## 📋 部署步骤

### 第一步：推送代码到GitHub

```bash
# 1. 进入项目目录
cd D:\AItest\recipe-app

# 2. 初始化Git（如果还没有）
git init

# 3. 添加所有文件
git add .

# 4. 提交
git commit -m "Ready to deploy on Render"

# 5. 创建GitHub仓库
# 去 https://github.com/new
# 创建仓库：recipe-app

# 6. 推送到GitHub
git remote add origin https://github.com/你的用户名/recipe-app.git
git branch -M main
git push -u origin main
```

---

### 第二步：在Render部署

#### 1. 注册Render账号

访问：https://render.com

点击 **Sign Up** → 用GitHub账号登录

#### 2. 创建Web Service

1. 点击 **New +** 按钮
2. 选择 **Web Service**
3. 连接你的GitHub仓库：**recipe-app**
4. 点击 **Connect**

#### 3. 配置Web Service

填写以下信息：

```
Name: recipe-app
（或任何你喜欢的名字）

Region: Singapore
（选择离中国近的）

Branch: main
（默认分支）

Root Directory: 留空
（使用整个仓库）

Environment: Python 3
（会自动检测）

Build Command:
pip install -r backend/requirements.txt

Start Command:
cd backend && gunicorn app:app --bind 0.0.0.0:$PORT

Plan: Free
（选择免费套餐）
```

#### 4. 环境变量（可选）

如果需要使用硅基流动API：

- 点击 **Advanced**
- 添加环境变量：
  ```
  Key: SILICONFLOW_API_KEY
  Value: 你的新API_Key
  ```

#### 5. 开始部署

点击 **Create Web Service**

等待5-10分钟，部署完成！

---

### 第三步：访问你的网站

部署完成后，Render会给你一个免费域名：

```
https://recipe-app-xxxx.onrender.com
```

点击这个链接，就能看到你的菜谱系统了！

---

## 🌐 绑定自定义域名（可选）

等你的域名实名认证完成后：

### 1. 在Render添加自定义域名

1. 进入你的Web Service
2. 点击 **Settings** 标签
3. 找到 **Custom Domain** 部分
4. 点击 **Add Custom Domain**
5. 输入你的域名：`recipe.com` 或 `www.recipe.com`
6. 点击 **Save**

### 2. 在域名服务商添加DNS解析

去你买域名的地方（阿里云/腾讯云等）：

#### 如果域名是 `www.recipe.com`：

```
类型：CNAME
主机记录：www
记录值：recipe-app-xxxx.onrender.com
TTL：10分钟
```

#### 如果域名是 `recipe.com`（裸域名）：

```
类型：A
主机记录：@
记录值：Render提供的IP地址（在Render设置页面查看）
TTL：10分钟
```

### 3. 等待DNS生效

- 通常5-30分钟
- 最长48小时
- 可以用工具检查：https://dnschecker.org

### 4. 自动获得SSL证书

DNS生效后，Render会自动：
- 检测域名指向
- 申请Let's Encrypt证书
- 配置https
- 完成！

---

## 🔄 自动更新

以后更新代码只需要：

```bash
# 1. 修改代码
# 2. 提交并推送
git add .
git commit -m "Update features"
git push

# 3. Render自动检测并重新部署
# 无需手动操作！
```

---

## 📊 查看日志和状态

### 查看部署日志

1. 进入你的Web Service
2. 点击 **Logs** 标签
3. 实时查看运行日志

### 查看服务状态

在Dashboard可以看到：
- CPU使用率
- 内存使用
- 请求数量
- 响应时间

---

## 🐛 常见问题

### Q1: 部署失败怎么办？

**查看Logs**，常见原因：
- Python版本不对 → 检查 `runtime.txt`
- 依赖安装失败 → 检查 `requirements.txt`
- 路径错误 → 检查Start Command

### Q2: 网站访问很慢？

免费套餐休眠了：
- 首次访问需要30秒唤醒
- 之后正常速度
- 解决方法：用定时ping服务（如UptimeRobot）每14分钟访问一次

### Q3: 无法访问API？

检查CORS配置：
- 已经在 `app.py` 中配置了 `CORS(app)`
- 应该可以正常访问

### Q4: 想要更好的性能？

升级到付费套餐：
- Starter: $7/月
- 不会休眠
- 更好性能

---

## 💡 优化建议

### 1. 保持服务激活

使用 **UptimeRobot** 免费监控：
- 访问 https://uptimerobot.com
- 添加你的Render域名
- 每5分钟ping一次
- 防止休眠

### 2. 优化加载速度

```python
# 在 app.py 中添加缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_recipes():
    return load_recipes()
```

### 3. 添加favicon

在 `frontend` 目录添加 `favicon.ico` 文件

---

## 📈 成本总结

```
域名：~60元/年（已购买）
Render：¥0/年（永久免费）
SSL证书：¥0/年（自动）
─────────────────────
总计：60元/年 ✅

对比买服务器：210元/年
省了：150元/年！
```

---

## ✅ 部署完成检查清单

- [ ] 代码推送到GitHub
- [ ] Render部署成功
- [ ] 可以访问默认域名
- [ ] 所有功能正常
- [ ] （可选）绑定自定义域名
- [ ] （可选）配置UptimeRobot防休眠

---

## 🎉 完成！

现在你有了：
- ✅ 完全免费的托管
- ✅ 自动SSL证书（https）
- ✅ 自动部署（推代码就更新）
- ✅ 可以绑定自己的域名

**祝使用愉快！** 🎊
