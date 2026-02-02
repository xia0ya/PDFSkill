# Render.com 部署指南

## 部署步骤

### 1. 准备 GitHub 仓库
将项目文件上传到 GitHub 仓库：
```
.
├── app.py                 # 主应用文件
├── requirements.txt      # Python 依赖
├── Procfile             # 启动配置
└── README.md            # 说明文件
```

### 2. 注册 Render.com 账户
- 访问 https://render.com
- 使用 GitHub 账户登录

### 3. 创建 Web Service
- 点击 "New +" 按钮
- 选择 "Web Service"
- 连接你的 GitHub 账户
- 选择包含项目的仓库

### 4. 配置部署设置
- **Environment**: Python
- **Branch**: main (或你的默认分支)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
- **Region**: 选择靠近用户的地区 (如 Singapore 适合亚洲用户)

### 5. 配置环境变量（可选）
如果需要，可在 Render 控制台设置环境变量。

### 6. 部署
- 点击 "Create Web Service"
- Render 会自动构建和部署应用

## 项目文件说明

### app.py
包含完整的 Flask 应用，支持：
- PDF 标签批量处理
- 9种位置选择
- 自定义标签文本、字体、颜色
- 单文件直接下载，多文件ZIP打包

### requirements.txt
```
Flask==2.3.3
PyPDF2==3.0.1
reportlab==4.0.4
gunicorn==21.2.0
Werkzeug==2.3.7
```

### Procfile
```
web: gunicorn --bind 0.0.0.0:$PORT app:app
```

## 注意事项

- Render 免费套餐每月提供 550 小时运行时间
- 应用在 15 分钟无请求后会进入休眠状态
- 首次访问可能需要几秒钟唤醒时间
- 文件上传大小受免费套餐限制

## 自定义域名（可选）
- 在 Render 控制台可以添加自定义域名
- 按照指示配置 DNS 记录