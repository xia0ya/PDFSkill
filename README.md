# PDF标签工具 - Render.com 部署包

## 文件说明

此文件夹包含在 Render.com 上部署 PDF 标签工具所需的所有文件：

- `app.py` - 主应用文件，包含完整的Flask应用
- `requirements.txt` - Python依赖包列表
- `Procfile` - Render启动配置
- `RENDER_DEPLOYMENT_GUIDE.md` - 详细部署指南

## 部署步骤

1. 将这些文件上传到你的GitHub仓库
2. 访问 https://render.com 并连接你的GitHub账户
3. 创建新的Web Service，选择你的仓库
4. Render会自动检测到Python环境和Procfile配置
5. 按照提示完成部署

## 功能特性

- 批量PDF标签处理
- 9种预设标签位置
- 自定义标签文本、字体、颜色
- 智能处理：单文件直接下载，多文件ZIP打包
- 响应式界面，支持移动端

## 注意事项

- 免费套餐每月有550小时运行时间
- 应用闲置后会休眠，首次访问可能稍慢
- 文件大小受到免费套餐限制

享受你的免费PDF标签工具部署！