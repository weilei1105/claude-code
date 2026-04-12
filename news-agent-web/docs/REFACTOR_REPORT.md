# 新闻抓取报告生成器 - 后端重构说明

## 重构概述

本项目后端已完全重写，从原来的 **Python scrapling 库直接调用** 模式改为 **Claude Code CLI + /scrapling-official skill** 模式。

## 架构变化

### 重构前
```
Vue.js Frontend → FastAPI Backend → scrapling Python库 → 目标网站
                                                      ↓
                                              Anthropic API (AI分析)
```

### 重构后
```
Vue.js Frontend → FastAPI Backend → Claude Code CLI → /scrapling-official skill → 目标网站
                                                      ↓
                                              Claude AI (内置分析)
```

## 核心改动

### 1. 依赖简化

**原 requirements.txt:**
```txt
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.0
scrapling>=0.4.5        # 直接依赖
anthropic>=0.18.0       # AI 分析
```

**新 requirements.txt:**
```txt
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.0
```

移除了 `scrapling` 和 `anthropic` 依赖，改为调用 Claude Code CLI。

### 2. 报告生成流程

**原流程:**
1. 搜索 URL 列表
2. 逐个抓取网页内容
3. 计算相关度过滤
4. 调用 Anthropic API 生成分析报告

**新流程:**
1. 调用 Claude Code CLI
2. 执行 `/scrapling-official` skill
3. Claude Code 自动完成搜索、抓取、分析
4. 返回 Markdown 格式报告

### 3. 关键代码

**server/main.py - 核心调用:**

```python
async def run_scrapling_skill(topic: str, max_articles: int = 10) -> tuple[str, str]:
    """
    调用 Claude Code CLI 执行 /scrapling-official skill 生成报告
    """
    prompt = f"""使用 /scrapling-official skill 生成关于「{topic}」的行业趋势分析报告。

要求：
1. 搜索并抓取最新的相关行业资讯
2. 分析市场趋势、竞争格局、技术发展
3. 生成结构化的 Markdown 格式报告
4. 报告应包含：行业概述、市场分析、竞争格局、技术趋势、风险挑战、结论建议
5. 列出信息来源链接
"""

    # 调用 Claude Code CLI
    process = await asyncio.create_subprocess_exec(
        CLAUDE_CODE_PATH,
        "--print",
        prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
    return parse_skill_output(stdout.decode('utf-8'))
```

## 环境要求

### 前端
- Node.js 18+
- npm

### 后端
- Python 3.10+
- FastAPI
- **Claude Code CLI** (必须安装并可执行)

### Claude Code CLI 安装

确保 `claude` 命令可用：

```bash
# macOS/Linux
brew install anthropic/claude-code/claude-code

# 或通过 npm
npm install -g @anthropic-ai/claude-code

# Windows
# 下载安装包或使用 scoop
scoop install claude-code
```

环境变量配置：
```bash
export CLAUDE_CODE_PATH=/path/to/claude  # 可选，默认 "claude"
```

## 启动方式

### 开发模式

```bash
cd news-agent-web

# 安装前端依赖
npm install

# 安装后端依赖
pip install -r server/requirements.txt

# 启动后端（终端1）
cd server
python main.py

# 启动前端（终端2）
npm run dev
```

### 生产模式

```bash
# 构建前端
npm run build

# 启动服务
cd server
python main.py
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/generate` | POST | 启动报告生成任务 |
| `/api/status/{task_id}` | GET | 获取任务状态和报告内容 |
| `/api/report/{task_id}` | GET | 下载报告文件 |
| `/api/reports` | GET | 列出已生成的报告 |
| `/api/stop/{task_id}` | POST | 停止运行中的任务 |

### 请求示例

```bash
# 启动报告生成
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "新能源汽车2026行业趋势", "max_articles": 10}'

# 查询状态
curl http://localhost:8000/api/status/{task_id}

# 下载报告
curl -O http://localhost:8000/api/report/{task_id}
```

## 前端适配

重构后的后端返回的报告格式已简化，前端需要相应调整。由于报告内容现在由 Claude Code 直接生成完整 Markdown，前端可以直接展示。

主要变化：
1. 移除了文章列表展示（因为报告已整合所有内容）
2. 直接展示 AI 生成的完整报告
3. 简化了状态跟踪逻辑

## 优势

1. **零爬虫代码**: 不需要在后端维护复杂的爬虫逻辑
2. **智能分析**: 利用 Claude Code 的 AI 能力进行内容分析和总结
3. **反爬虫绕过**: scrapling skill 内置反检测和 Cloudflare 绕过
4. **维护简单**: 只需调用 Claude Code，无需管理多个依赖
5. **可扩展性**: 可以轻松添加更多分析维度

## 注意事项

1. **执行时间**: 完整报告生成可能需要 1-3 分钟
2. **并发限制**: 建议限制同时执行的任务数（当前限制为 3）
3. **网络要求**: 需要能够访问 Claude Code 服务器
4. **成本**: 使用 Claude Code API 产生费用（按 token 计费）

## 故障排除

### "找不到 Claude Code CLI"
```bash
# 检查 claude 是否安装
which claude
claude --version

# 设置路径
export CLAUDE_CODE_PATH=/usr/local/bin/claude
```

### 报告生成超时
当前超时设置为 5 分钟，如果目标网站响应慢可能导致超时。可以：
1. 减少 `max_articles` 数量
2. 检查网络连接
3. 查看 Claude Code 日志

### 前端无法连接后端
检查 CORS 配置是否允许前端域名访问。

---

*文档更新时间: 2026-04-11*
