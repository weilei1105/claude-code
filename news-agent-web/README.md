# 新闻抓取报告生成器 Web版

基于 Vue3 + FastAPI 的智能新闻抓取工具，输入主题即可自动搜索、抓取、生成报告。

## 功能特点

- 🔍 多源搜索：百度、搜狗、360、知乎、36kr、新浪等
- 📰 行业垂直：能源电力、科技、财经、政府政策
- ⚡ 异步并发：高速抓取，支持断点续传
- 📊 实时进度：抓取过程一目了然
- 📥 Markdown报告：一键下载

## 快速开始

### 1. 安装依赖

```bash
# 前端
cd news-agent-web
npm install

# 后端
cd server
pip install -r requirements.txt
```

### 2. 配置Scrapling路径

编辑 `server/main.py`，修改第15行的 Scrapling 路径：

```python
SCRAPLING_PATH = r"C:\Users\YourUser\AppData\Local\Programs\Python\Python311\Scripts\scrapling.exe"
```

### 3. 启动服务

```bash
# 方式一：一键启动（前后端同时运行）
npm start

# 方式二：分别启动
# 终端1：启动后端
cd server
python main.py

# 终端2：启动前端
npm run dev
```

### 4. 访问

打开浏览器访问 http://localhost:5173

## 使用说明

### 基本用法

1. 输入搜索主题（如：电力行业政策）
2. 选择搜索源（默认百度）
3. 点击"开始抓取"
4. 等待完成后下载报告

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --source | 搜索源 | auto |
| --industry | 行业垂直 | 无 |
| --max | 最大文章数 | 10 |

### 搜索源

- `baidu` - 百度搜索
- `sogou` - 搜狗搜索
- `360` - 360搜索
- `zhihu` - 知乎搜索
- `36kr` - 36氪搜索
- `sina` - 新浪搜索
- `bing` - Bing搜索
- `all` - 全源搜索

### 行业垂直

- `能源电力` - 国家能源局、中国电力企业联合会等
- `科技` - 36kr、凤凰网、新浪科技
- `财经` - 新浪财经、第一财经、界面新闻
- `政府政策` - 中国政府网、发改委、工信部

## 项目结构

```
news-agent-web/
├── src/
│   ├── App.vue          # 主组件
│   └── main.js         # 入口
├── server/
│   └── main.py         # FastAPI后端
├── index.html
├── package.json
└── vite.config.js
```

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/crawl` | POST | 启动抓取任务 |
| `/api/status/{task_id}` | GET | 获取任务状态 |
| `/api/report` | GET | 下载报告 |
| `/api/articles` | GET | 获取文章列表 |

## 部署

### Docker部署

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY server/requirements.txt .
RUN pip install -r requirements.txt
COPY server/ .
EXPOSE 8000
CMD ["python", "main.py"]
```

### Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5173;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

## 系统要求

- Python 3.10+
- Node.js 18+
- Scrapling >= 0.4.5

## 许可证

MIT
