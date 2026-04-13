"""Report generation service with Claude Code CLI integration."""

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from app.config import settings


# ============== Report Type Definitions ==============
REPORT_TYPES = {
    "trend": "趋势分析报告",
    "compare": "对比分析报告",
    "comprehensive": "综合评估报告",
    "policy": "政策解读报告",
}


# ============== Data Classes ==============
@dataclass
class TaskStatus:
    """Task status tracking."""

    task_id: str
    status: str  # running, completed, failed, stopped, partial
    progress_percent: int = 0
    status_message: str = ""
    report_content: str = ""
    error: str = ""
    stopped: bool = False
    start_time: float = 0
    elapsed_seconds: int = 0


# ============== Task Storage ==============
tasks: dict[str, TaskStatus] = {}


# ============== Topic Polishing ==============
def polish_topic(topic: str, report_type: str) -> str:
    """Polish user input topic into a proper report title."""
    # Common industry suffixes
    industry_suffixes = ["行业", "市场", "产业", "领域"]
    # Check if topic already has a suitable suffix
    has_suffix = any(topic.endswith(s) for s in industry_suffixes + ["分析", "趋势", "报告"])

    if has_suffix:
        return topic

    # Add appropriate suffix based on report type
    polish_map = {
        "trend": "行业趋势分析",
        "compare": "市场对比分析",
        "comprehensive": "综合评估报告",
        "policy": "政策解读",
    }

    suffix = polish_map.get(report_type, "行业分析")
    # Handle topics that are already complete phrases
    if len(topic) <= 6:
        return topic + suffix
    else:
        return topic + "：" + suffix


# ============== Prompt Templates ==============
def generate_prompt(topic: str, report_type: str, depth: str = "simple") -> str:
    """Generate prompt based on report type and depth."""

    polished_topic = polish_topic(topic, report_type)

    simple_prompts = {
        "trend": (
            "使用 /scrapling-official skill 生成关于「" + topic + "」的趋势分析报告。\n\n"
            "重要：直接在命令行输出 Markdown 格式的报告内容，不要保存任何文件！\n\n"
            "要求：\n"
            "1. 搜索并抓取3-5个关键信息源\n"
            "2. 分析核心趋势和要点\n"
            "3. 输出完整的 Markdown 报告内容\n\n"
            "报告结构（3章，每章至少3段）：\n"
            "# " + polished_topic + "\n\n"
            "## 一、行业现状\n"
            "## 二、核心趋势\n"
            "## 三、发展展望\n\n"
        ),
        "compare": (
            "使用 /scrapling-official skill 生成关于「" + topic + "」的对比分析报告。\n\n"
            "重要：直接在命令行输出 Markdown 格式的报告内容，不要保存任何文件！\n\n"
            "要求：\n"
            "1. 搜索并抓取主要对比对象的信息\n"
            "2. 对比分析核心差异\n"
            "3. 输出完整的 Markdown 报告内容\n\n"
            "报告结构（3章，每章至少3段）：\n"
            "# " + polished_topic + "\n\n"
            "## 一、对比对象概述\n"
            "## 二、核心对比\n"
            "## 三、结论\n\n"
        ),
        "comprehensive": (
            "使用 /scrapling-official skill 生成关于「" + topic + "」的综合评估报告。\n\n"
            "重要：直接在命令行输出 Markdown 格式的报告内容，不要保存任何文件！\n\n"
            "要求：\n"
            "1. 搜索并抓取关键维度的信息\n"
            "2. 进行综合评估\n"
            "3. 输出完整的 Markdown 报告内容\n\n"
            "报告结构（3章，每章至少3段）：\n"
            "# " + polished_topic + "\n\n"
            "## 一、评估概述\n"
            "## 二、核心发现\n"
            "## 三、结论与建议\n\n"
        ),
        "policy": (
            "使用 /scrapling-official skill 生成关于「" + topic + "」的政策解读报告。\n\n"
            "重要：直接在命令行输出 Markdown 格式的报告内容，不要保存任何文件！\n\n"
            "要求：\n"
            "1. 搜索并抓取政策文件和解读\n"
            "2. 解读核心内容和影响\n"
            "3. 输出完整的 Markdown 报告内容\n\n"
            "报告结构（3章，每章至少3段）：\n"
            "# " + polished_topic + "\n\n"
            "## 一、政策概述\n"
            "## 二、核心内容\n"
            "## 三、影响与建议\n\n"
        ),
    }

    depth_prompts = {
        "trend": (
            "使用 /scrapling-official skill 生成关于「" + topic + "」的趋势分析报告。\n\n"
            "要求：\n"
            "1. 搜索并抓取最新的相关行业资讯、市场数据、政策动态\n"
            "2. 分析行业发展趋势、增长驱动因素、市场变化规律\n"
            "3. 识别关键转折点和潜在风险\n"
            "4. 预测未来1-3年的发展方向\n"
            "5. 直接输出完整 Markdown 内容，禁止保存任何文件！\n\n"
            "报告结构：\n"
            "# " + polished_topic + "\n\n"
            "## 一、行业现状概述\n"
            "## 二、市场趋势分析\n"
            "## 三、驱动因素与制约因素\n"
            "## 四、发展预测与展望\n"
            "## 五、风险预警\n"
            "## 六、结论与建议\n\n"
            "信息来源必须包含权威机构数据和专家观点。"
        ),
        "compare": (
            "使用 /scrapling-official skill 生成关于「" + topic + "」的对比分析报告。\n\n"
            "要求：\n"
            "1. 搜索并抓取多个竞争主体或产品的相关资讯\n"
            "2. 对比分析各方的优劣势、市场表现、技术特点\n"
            "3. 找出差异化和共同点\n"
            "4. 给出客观的对比结论\n"
            "5. 直接输出完整 Markdown 内容，禁止保存任何文件！\n\n"
            "报告结构：\n"
            "# " + polished_topic + "\n\n"
            "## 一、对比对象概述\n"
            "## 二、核心指标对比\n"
            "### 2.1 市场规模与份额\n"
            "### 2.2 技术实力对比\n"
            "### 2.3 产品矩阵对比\n"
            "### 2.4 定价策略对比\n"
            "### 2.5 渠道布局对比\n"
            "## 三、优势分析\n"
            "## 四、劣势分析\n"
            "## 五、综合评价与结论\n\n"
            "对比对象应涵盖行业主要玩家，确保客观公正。"
        ),
        "comprehensive": (
            "使用 /scrapling-official skill 生成关于「" + topic + "」的综合评估报告。\n\n"
            "要求：\n"
            "1. 搜索并抓取全面的相关资讯：政策、市场、技术、企业、案例等\n"
            "2. 从多维度进行系统性评估\n"
            "3. 既有定性分析也有定量数据\n"
            "4. 给出综合评分或评级\n"
            "5. 直接输出完整 Markdown 内容，禁止保存任何文件！\n\n"
            "报告结构：\n"
            "# " + polished_topic + "\n\n"
            "## 一、评估对象定义\n"
            "## 二、评估维度与指标体系\n"
            "## 三、政策环境评估\n"
            "## 四、市场前景评估\n"
            "## 五、技术成熟度评估\n"
            "## 六、竞争格局评估\n"
            "## 七、风险评估\n"
            "## 八、综合评级与结论\n"
            "## 九、建议与展望\n\n"
            "评估应基于充分的数据和事实，结论需有理有据。"
        ),
        "policy": (
            "使用 /scrapling-official skill 生成关于「" + topic + "」的政策解读报告。\n\n"
            "要求：\n"
            "1. 搜索并抓取最新的相关政策法规、官方解读、行业反应\n"
            "2. 详细解读政策背景，主要内容、适用范围\n"
            "3. 分析对行业、市场、企业的具体影响\n"
            "4. 预测政策后续走向和配套措施\n"
            "5. 直接输出完整 Markdown 内容，禁止保存任何文件！\n\n"
            "报告结构：\n"
            "# " + polished_topic + "\n\n"
            "## 一、政策概述\n"
            "### 1.1 政策背景\n"
            "### 1.2 政策目标\n"
            "### 1.3 适用范围\n"
            "## 二、核心内容解读\n"
            "## 三、关键条款分析\n"
            "## 四、影响评估\n"
            "### 4.1 对行业的影响\n"
            "### 4.2 对市场的影响\n"
            "### 4.3 对企业的影响\n"
            "## 五、市场反应与动态\n"
            "## 六、政策趋势展望\n"
            "## 七、企业应对建议\n"
            "## 八、结论\n\n"
            "政策解读需准确权威，引用原文关键表述。"
        ),
    }

    prompts = simple_prompts if depth == "simple" else depth_prompts
    default_prompt = (
        "使用 /scrapling-official skill 生成关于「" + topic + "」的行业分析报告。\n\n"
        "要求：\n"
        "1. 搜索并抓取最新的相关资讯\n"
        "2. 进行全面深入的分析\n"
        "3. 生成结构化的 Markdown 格式报告\n\n"
        "请开始执行。"
    )

    return prompts.get(report_type, default_prompt)


# ============== Utility Functions ==============
def sanitize_topic(topic: str) -> str:
    """Sanitize topic string for filename."""
    return re.sub(r'[^\w\s-]', '', topic)[:30].strip()


def parse_skill_output(output: str) -> tuple:
    """Parse Claude CLI output to extract report content."""
    if not output:
        return "", "Skill 执行无输出"

    lines = output.split('\n')
    report_lines = []
    started = False

    for line in lines:
        # Skip empty lines before report starts
        if not started:
            # Skip info messages like "好消息：", "使用 scrapling", etc.
            if not line.strip():
                continue
            if line.strip().startswith('event:') or line.strip().startswith('data:'):
                continue
            # Skip known non-content prefixes
            skip_prefixes = ['好消息', '坏消息', '使用', '正在', '错误', 'error', 'failed', 'warning', 'info']
            if any(line.strip().lower().startswith(p.lower()) for p in skip_prefixes):
                continue
            # Skip lines that are clearly not markdown headings
            stripped = line.strip()
            if not stripped.startswith('# ') and not stripped.startswith('## '):
                # Check if it looks like a log/info line
                if ':' in stripped and len(stripped) < 100:
                    continue
                # Check if it's a skill invocation line
                if stripped.startswith('/') or 'skill' in stripped.lower():
                    continue

        # Start capturing from first markdown heading or content
        if not started:
            if line.strip().startswith('# ') or line.strip().startswith('## '):
                started = True
            elif line.strip() and not line.startswith('event:') and not line.startswith('data:'):
                # Skip lines that are too short or look like system messages
                if len(line.strip()) > 20 and not any(c in line for c in ['$', '>', '→', '•']):
                    started = True

        if started:
            report_lines.append(line)

    report = '\n'.join(report_lines).strip()

    # If still empty, try to find any content starting with # heading
    if not report:
        for i, line in enumerate(lines):
            if line.strip().startswith('# ') or line.strip().startswith('## '):
                report = '\n'.join(lines[i:]).strip()
                break

    if not report and output:
        error_patterns = ['error', 'failed', 'not found', 'permission denied']
        for pattern in error_patterns:
            if pattern in output.lower():
                return "", "Skill 执行出错: " + output[:500]

    return report, ""


# ============== Stream Generator ==============
async def generate_report_stream(
    task_id: str, topic: str, report_type: str, report_depth: str
) -> AsyncGenerator[str, None]:
    """Generate report with SSE streaming."""
    task = tasks.get(task_id)
    if not task:
        return

    task.start_time = time.time()
    task.status_message = "生成报告..."
    task.progress_percent = 5

    start_time = time.time()
    timeout = settings.depth_timeout if report_depth == "depth" else settings.simple_timeout

    yield f"event: progress\ndata: 正在准备...\n\n"

    try:
        prompt = generate_prompt(topic, report_type, report_depth)
        depth_text = "简要" if report_depth == "simple" else "深度"
        yield f"event: progress\ndata: 正在生成{depth_text}报告...\n\n"

        # Start Claude process
        process = await asyncio.create_subprocess_exec(
            settings.bun_path,
            settings.claude_cli,
            "-p",
            "--dangerously-skip-permissions",
            prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=settings.claude_code_dir,
            env={**__import__("os").environ},
        )

        # Monitor process with heartbeat
        process_task = asyncio.create_task(process.communicate())
        output = ""
        last_heartbeat = 0

        while not process_task.done():
            try:
                await asyncio.wait_for(asyncio.shield(process_task), timeout=15)
            except asyncio.TimeoutError:
                elapsed_now = int(time.time() - start_time)
                if elapsed_now - last_heartbeat >= settings.heartbeat_interval:
                    yield f"event: progress\ndata: 生成中... ({elapsed_now}秒)\n\n"
                    last_heartbeat = elapsed_now

        # Get process result
        try:
            stdout, stderr = process_task.result()
            output = stdout.decode('utf-8', errors='ignore')
            if stderr:
                stderr_text = stderr.decode('utf-8', errors='ignore')
                if stderr_text and 'error' in stderr_text.lower():
                    print("Claude stderr:", stderr_text[:200])
        except Exception as e:
            yield f"event: error\ndata: 生成失败: {str(e)}\n\n"
            return

        elapsed = int(time.time() - start_time)

        if not output.strip():
            yield f"event: error\ndata: 生成无结果\n\n"
            return

        # Parse report content
        report, parse_error = parse_skill_output(output)

        task.report_content = report if report else output
        task.status = "completed"
        task.progress_percent = 100
        task.elapsed_seconds = elapsed

        yield f"event: complete\ndata: {json.dumps({'status': 'completed', 'content': task.report_content, 'elapsed': elapsed})}\n\n"

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        yield f"event: error\ndata: {str(e)}\n\n"


def get_task(task_id: str) -> Optional[TaskStatus]:
    """Get task by ID."""
    return tasks.get(task_id)


def create_task(task_id: str, topic: str, report_type: str) -> TaskStatus:
    """Create a new task."""
    task = TaskStatus(
        task_id=task_id,
        status="running",
        progress_percent=0,
        status_message=f"准备生成{REPORT_TYPES.get(report_type, '报告')}...",
        start_time=time.time(),
    )
    tasks[task_id] = task
    return task


def stop_task(task_id: str) -> bool:
    """Stop a running task."""
    task = tasks.get(task_id)
    if not task or task.status not in ["running", "partial"]:
        return False

    task.stopped = True
    task.status = "stopped"
    task.status_message = "已停止"
    return True
