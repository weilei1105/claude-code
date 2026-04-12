# News Agent Web - 智能报告生成系统

## 1. Concept & Vision

一个基于 AI 的智能报告生成平台，用户输入主题即可自动抓取最新资讯并生成结构化分析报告。核心差异化：无需手动搜索，AI 自动完成信息收集、分析、报告生成的完整流程。

**目标用户**：行业研究人员、投资者、内容创作者、企业战略部门

## 2. Design Language

### 色彩系统
- **Primary**: `#1a1a2e` (深海军蓝)
- **Secondary**: `#0f3460` (皇家蓝)
- **Accent**: `#10b981` (翡翠绿，用于成功/下载)
- **Background**: `#f8fafc` (冷灰白)
- **Surface**: `#ffffff`
- **Text Primary**: `#1a1a2e`
- **Text Secondary**: `#64748b`
- **Error**: `#dc2626`

### 字体
- 主字体：`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- 代码字体：`'SFMono-Regular', Consolas, 'Liberation Mono', monospace`

### 圆角 & 阴影
- 卡片圆角：16px
- 按钮圆角：12px
- 输入框圆角：12px
- 阴影：`0 4px 20px rgba(0,0,0,0.08)`

## 3. Layout & Structure

### 页面结构
```
┌─────────────────────────────────────┐
│           Header (渐变背景)          │
│     📊 智能报告生成器                 │
│     基于 Scrapling + Claude AI        │
├─────────────────────────────────────┤
│                                     │
│   ┌─────────────────────────────┐   │
│   │     输入区域 (白色卡片)        │   │
│   │   [主题输入] [报告类型]       │   │
│   │   [报告深度] [生成按钮]      │   │
│   └─────────────────────────────┘   │
│                                     │
│   ┌─────────────────────────────┐   │
│   │     进度区域 (加载状态)       │   │
│   └─────────────────────────────┘   │
│                                     │
│   ┌─────────────────────────────┐   │
│   │     报告展示 (Markdown)        │   │
│   │   [下载按钮]                  │   │
│   └─────────────────────────────┘   │
│                                     │
├─────────────────────────────────────┤
│              Footer                 │
└─────────────────────────────────────┘
```

### 响应式策略
- 最大宽度：1000px，居中
- 移动端：单列布局，padding 缩小

## 4. Features & Interactions

### 报告类型
| 类型 | 说明 |
|------|------|
| `trend` | 趋势分析报告 |
| `compare` | 对比分析报告 |
| `comprehensive` | 综合评估报告 |
| `policy` | 政策解读报告 |

### 报告深度
| 模式 | 章节数 | 耗时 | 说明 |
|------|--------|------|------|
| `simple` | 3-4章 | 3-5分钟 | 简要报告 |
| `depth` | 6-9章 | 8-15分钟 | 深度报告 |

### 交互流程
1. 用户输入主题 → 选择报告类型 → 选择深度 → 点击生成
2. 显示实时进度（已用时间、预估剩余时间）
3. 生成完成后显示报告，支持 Markdown 渲染
4. 支持一键下载报告为 .md 文件

### 错误处理
- 网络错误：显示友好提示
- 生成失败：显示错误原因
- 超时：提示用户可以尝试深度模式或缩短主题

## 5. Component Inventory

### InputSection
- 主题输入框（placeholder 提示示例主题）
- 报告类型单选按钮组（4选1）
- 报告深度单选按钮组（2选1）
- 生成按钮（loading 状态禁用）

### ProgressSection
- 旋转动画 spinner
- 状态文本（实时更新）
- 时间信息徽章（已用时间、预估剩余）
- 进度条（百分比显示）

### ReportSection
- 报告标题 + 生成耗时徽章
- Markdown 内容渲染区（代码高亮、表格样式）
- 下载按钮

### ErrorSection
- 红色背景错误提示

## 6. Technical Approach

### 前端
- **框架**：Vue 3 (Composition API)
- **构建**：Vite 5
- **Markdown**：marked + highlight.js
- **HTTP**：原生 fetch + SSE 流式读取

### 后端
- **框架**：FastAPI
- **AI 集成**：Claude Code CLI (`/scrapling-official` skill)
- **进程管理**：asyncio subprocess + 进程池预热
- **超时**：180s (simple) / 600s (depth)

### API Design

#### POST /api/generate
启动报告生成（流式响应）

Request:
```json
{
  "topic": "新能源汽车",
  "report_type": "compare",
  "report_depth": "simple",
  "max_articles": 10
}
```

Response: SSE stream
```
event: progress
data: 正在生成简要报告...

event: complete
data: {"status": "completed", "content": "# 新能源汽车对比分析报告\n\n...", "elapsed": 156}

event: error
data: 生成失败: 原因
```

#### GET /api/report-types
获取支持的报告类型列表

Response:
```json
{
  "report_types": {
    "trend": "趋势分析报告",
    "compare": "对比分析报告",
    "comprehensive": "综合评估报告",
    "policy": "政策解读报告"
  }
}
```

#### GET /api/status/{task_id}
获取任务状态

#### POST /api/stop/{task_id}
停止运行中的任务

#### GET /api/health
健康检查

## 7. Architecture

### 项目结构
```
news-agent-web/
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/          # API 服务层
│   │   ├── components/    # Vue 组件
│   │   ├── utils/        # 工具函数
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── server/                # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py       # FastAPI 入口
│   │   ├── config.py     # 配置管理
│   │   ├── api/          # API 路由
│   │   │   └── routes.py
│   │   ├── models/       # Pydantic 模型
│   │   │   └── schemas.py
│   │   └── services/     # 业务逻辑
│   │       └── report_generator.py
│   ├── tests/            # 单元测试
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
└── README.md
```

### Docker 部署
- Frontend: Nginx 生产构建
- Backend: Python + Uvicorn
- 通过 docker-compose 编排

### 环境变量
| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CLAUDE_CODE_PATH` | Claude Code CLI 路径 | `C:/Users/Administrator/claude-code` |
| `SERVER_PORT` | 后端端口 | `8000` |
| `FRONTEND_PORT` | 前端端口 | `5173` |
