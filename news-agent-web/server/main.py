"""
新闻抓取报告生成器 - FastAPI后端服务
基于 /scrapling-official skill 调用 Claude Code CLI
"""

import asyncio
import os
import uuid
import re
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# ============== 配置 ==============
CLAUDE_CODE_DIR = os.environ.get("CLAUDE_CODE_PATH", "C:/Users/Administrator/claude-code")
BUN_PATH = "bun"
REPORTS_DIR = Path("generated_reports")
REPORTS_DIR.mkdir(exist_ok=True)

# ============== 数据结构 ==============
@dataclass
class TaskStatus:
    task_id: str
    status: str  # running, completed, failed, stopped
    progress: int
    status_message: str
    report_content: str = ""
    error: str = ""
    stopped: bool = False

# ============== 存储 ==============
tasks: dict = {}
executor = ThreadPoolExecutor(max_workers=3)

# ============== FastAPI ==============
app = FastAPI(title="新闻抓取报告生成器")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== 工具函数 ==============
def sanitize_topic(topic: str) -> str:
    """清理主题名称，用于文件名"""
    return re.sub(r'[^\w\s-]', '', topic)[:30].strip()

def parse_skill_output(output: str) -> tuple[str, str]:
    """
    解析 skill 输出，提取报告内容和错误信息
    返回 (report_content, error_message)
    """
    if not output:
        return "", "Skill 执行无输出"

    # 查找报告内容（通常在最后一个 markdown 代码块或文件输出之后）
    lines = output.split('\n')
    report_lines = []
    in_report = False

    for line in lines:
        # 检测报告开始
        if 'report_' in line.lower() and '.md' in line.lower():
            in_report = True
        # 检测错误
        if 'error' in line.lower() or 'failed' in line.lower():
            if not in_report:
                continue

        if in_report:
            report_lines.append(line)

    # 如果没有找到文件输出，尝试直接使用输出
    if not report_lines:
        # 查找以 # 开头的内容（markdown 标题）
        for i, line in enumerate(lines):
            if line.strip().startswith('# ') and i > 0:
                report_lines = lines[i:]
                break

    report = '\n'.join(report_lines).strip()

    # 如果仍然没有报告内容，返回原始输出（可能包含错误）
    if not report and output:
        # 检查是否有明显错误
        error_patterns = ['error', 'failed', 'not found', 'permission denied']
        for pattern in error_patterns:
            if pattern in output.lower():
                return "", f"Skill 执行出错: {output[:500]}"

    return report, ""

async def run_scrapling_skill(topic: str, max_articles: int = 10) -> tuple[str, str]:
    """
    调用 Claude Code CLI 执行 /scrapling-official skill 生成报告
    返回 (report_content, error_message)
    """
    try:
        # 构建 prompt
        prompt = f"""使用 /scrapling-official skill 生成关于「{topic}」的行业趋势分析报告。

要求：
1. 搜索并抓取最新的相关行业资讯
2. 分析市场趋势、竞争格局、技术发展
3. 生成结构化的 Markdown 格式报告
4. 报告应包含：行业概述、市场分析、竞争格局、技术趋势、风险挑战、结论建议
5. 列出信息来源链接

请开始执行。"""

        # 创建临时文件用于捕获输出
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp_path = tmp.name

        try:
            # 调用 Claude Code CLI (使用 bun run dev 从项目目录)
            process = await asyncio.create_subprocess_exec(
                BUN_PATH,
                "run",
                "dev",
                "--print",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=CLAUDE_CODE_DIR,
                env={**os.environ, "BUN_INSPECT": ""}
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)

            output = stdout.decode('utf-8', errors='ignore')

            # 如果有 stderr 错误，记录但继续处理
            if stderr:
                print(f"Claude Code stderr: {stderr.decode('utf-8', errors='ignore')}")

            # 解析输出
            report, error = parse_skill_output(output)
            return report, error

        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except:
                pass

    except asyncio.TimeoutError:
        return "", "Skill 执行超时（5分钟）"
    except FileNotFoundError:
        return "", f"找不到 Claude Code CLI: {CLAUDE_CODE_PATH}"
    except Exception as e:
        return "", f"执行出错: {str(e)}"

# ============== API ==============
class ReportRequest(BaseModel):
    topic: str
    max_articles: int = 10

@app.post("/api/generate")
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """启动报告生成任务"""
    task_id = uuid.uuid4().hex[:12]

    tasks[task_id] = TaskStatus(
        task_id=task_id,
        status="running",
        progress=0,
        status_message="正在启动报告生成..."
    )

    # 后台执行
    background_tasks.add_task(run_report_task, task_id, request.topic, request.max_articles)

    return {"task_id": task_id, "message": "报告生成任务已启动"}

@app.post("/api/stop/{task_id}")
async def stop_task(task_id: str):
    """停止任务"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    if task.status != "running":
        return {"message": "任务已结束，无法停止"}

    task.stopped = True
    task.status = "stopped"
    task.status_message = "已停止"

    return {"message": "停止成功"}

async def run_report_task(task_id: str, topic: str, max_articles: int):
    """执行报告生成任务"""
    try:
        task = tasks[task_id]
        task.status_message = "正在搜索和抓取资讯..."

        # 调用 scrapling skill
        report, error = await run_scrapling_skill(topic, max_articles)

        if task.stopped:
            task.status = "stopped"
            task.status_message = "已停止"
            return

        if error:
            task.status = "failed"
            task.error = error
            task.status_message = f"生成失败: {error[:100]}"
            return

        if not report:
            task.status = "failed"
            task.error = "未能生成报告内容"
            task.status_message = "生成失败：无报告内容"
            return

        # 保存报告
        safe_topic = sanitize_topic(topic)
        report_file = REPORTS_DIR / f"report_{safe_topic}_{task_id}.md"
        report_file.write_text(report, encoding="utf-8")

        task.report_content = report
        task.status = "completed"
        task.status_message = "报告生成完成"
        task.progress = 100

    except Exception as e:
        task = tasks[task_id]
        task.status = "failed"
        task.error = str(e)
        task.status_message = f"出错: {str(e)[:100]}"

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    return {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "status_message": task.status_message,
        "report_content": task.report_content if task.status == "completed" else "",
        "error": task.error
    }

@app.get("/api/report/{task_id}")
async def get_report(task_id: str):
    """下载报告文件"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    if task.status != "completed" or not task.report_content:
        raise HTTPException(status_code=404, detail="报告未生成")

    safe_topic = sanitize_topic(task.report_content[:50] if task.report_content else "report")
    filename = f"report_{safe_topic}_{datetime.now().strftime('%Y%m%d')}.md"

    return FileResponse(
        task.report_content.encode() if isinstance(task.report_content, str) else task.report_content,
        media_type="text/markdown",
        filename=filename
    )

@app.get("/api/reports")
async def list_reports():
    """列出已生成的报告"""
    reports = []
    for f in REPORTS_DIR.glob("*.md"):
        stat = f.stat()
        reports.append({
            "name": f.name,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "path": str(f)
        })
    return sorted(reports, key=lambda x: x["created"], reverse=True)[:20]

# ============== 启动 ==============
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
