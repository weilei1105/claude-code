# News Agent Web - 智能报告生成器

基于 AI 的专业报告生成系统，自动抓取最新资讯并生成结构化分析报告。

## 功能特性

- **智能报告生成**：输入主题，自动完成信息收集、分析、报告生成
- **多种报告类型**：趋势分析、对比分析、综合评估、政策解读
- **双深度模式**：简要报告（3-5分钟）和深度报告（8-15分钟）
- **实时进度**：SSE 流式响应，实时显示生成进度
- **Markdown 渲染**：支持代码高亮、表格等 Markdown 特性
- **一键下载**：生成完成后可直接下载 .md 文件

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite 5 |
| 后端 | FastAPI + Uvicorn |
| AI 集成 | Claude Code CLI + Scrapling |
| 部署 | Docker + Docker Compose |

## 快速开始

### 前置要求

- Node.js 18+
- Python 3.10+
- Bun (用于运行 Claude Code CLI)
- Claude Code CLI 已安装

### 本地开发

```bash
# 1. 克隆项目
git clone <repo-url>
cd news-agent-web

# 2. 安装前端依赖
npm install

# 3. 配置环境变量
cp server/.env.example server/.env
# 编辑 server/.env，设置 CLAUDE_CODE_PATH

# 4. 启动后端
cd server
pip install -r requirements.txt
python main.py

# 5. 启动前端（新终端）
npm run dev

# 6. 访问 http://localhost:5173
```

### Docker 部署

```bash
# 1. 配置环境变量
cp server/.env.example server/.env
# 编辑 server/.env

# 2. 启动所有服务
docker-compose up -d --build

# 3. 访问 http://localhost
```

## 项目结构

```
news-agent-web/
├── src/                  # Vue 3 前端源码
│   ├── App.vue         # 主应用组件
│   ├── main.js         # 入口文件
│   ├── api/            # API 服务层
│   └── components/     # Vue 组件
│
├── server/              # FastAPI 后端
│   ├── app/
│   │   ├── main.py     # FastAPI 入口
│   │   ├── config.py   # 配置管理
│   │   ├── api/        # API 路由
│   │   ├── models/     # Pydantic 模型
│   │   └── services/   # 业务逻辑
│   ├── tests/          # 单元测试
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml    # Docker Compose 配置
├── Dockerfile           # 前端构建
├── nginx.conf          # Nginx 配置
├── SPEC.md             # 项目规格说明
└── README.md
```

## API 文档

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/report-types` | 获取报告类型列表 |
| POST | `/api/generate` | 启动报告生成（流式） |
| GET | `/api/status/{task_id}` | 获取任务状态 |
| POST | `/api/stop/{task_id}` | 停止任务 |
| GET | `/api/report/{task_id}` | 下载报告文件 |
| GET | `/api/reports` | 列出已生成的报告 |

### 请求示例

```bash
# 生成简要对比分析报告
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "新能源汽车",
    "report_type": "compare",
    "report_depth": "simple"
  }'
```

## 配置说明

### 后端环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CLAUDE_CODE_PATH` | Claude Code CLI 路径 | `C:/Users/Administrator/claude-code` |
| `SERVER_PORT` | 服务端口 | `8000` |
| `PROCESS_POOL_SIZE` | 进程池大小 | `2` |
| `SIMPLE_TIMEOUT` | 简要报告超时(秒) | `300` |
| `DEPTH_TIMEOUT` | 深度报告超时(秒) | `900` |

## 开发指南

### 前端开发

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

### 后端开发

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
cd server
pip install -r requirements.txt

# 运行服务
python main.py

# 运行测试
pytest
```

## 生产部署

### Docker Compose (推荐)

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 系统要求

- Python 3.10+
- Node.js 18+
- Bun (Claude Code CLI 需要)
- Claude Code CLI 已安装并配置

## 许可证

MIT License
