"""API routes for report generation."""

import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.config import settings
from app.models import (
    ReportTypeResponse,
    ReportRequest,
    TaskStatusResponse,
    StopTaskResponse,
    HealthResponse,
    ReportsListResponse,
    ReportInfo,
)
from app.services import (
    REPORT_TYPES,
    generate_report_stream,
    get_task,
    create_task,
    stop_task,
    sanitize_topic,
)


# ============== Router ==============
router = APIRouter()


# ============== Endpoints ==============
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@router.get("/report-types", response_model=ReportTypeResponse)
async def get_report_types():
    """Get available report types."""
    return ReportTypeResponse(report_types=REPORT_TYPES)


@router.post("/generate", response_class=StreamingResponse)
async def generate_report(request: ReportRequest):
    """
    Start report generation with streaming response.

    Returns SSE stream with progress updates and final report content.
    """
    if request.report_type.value not in REPORT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="无效的报告类型。可选类型: " + str(list(REPORT_TYPES.keys())),
        )

    task_id = uuid.uuid4().hex[:12]
    create_task(task_id, request.topic, request.report_type.value)

    return StreamingResponse(
        generate_report_stream(
            task_id, request.topic, request.report_type.value, request.report_depth.value
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/stop/{task_id}", response_model=StopTaskResponse)
async def stop_task_endpoint(task_id: str):
    """Stop a running task."""
    from app.services import tasks

    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    if task.status not in ["running", "partial"]:
        return StopTaskResponse(message="任务已结束，无法停止")

    if stop_task(task_id):
        return StopTaskResponse(message="停止成功")
    else:
        raise HTTPException(status_code=400, detail="停止失败")


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_status(task_id: str):
    """Get task status."""
    from app.services import tasks

    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    elapsed = int(
        task.elapsed_seconds
        if task.elapsed_seconds
        else (time.time() - task.start_time if task.start_time else 0)
    )

    # Calculate remaining time
    remaining = 0
    if task.progress_percent > 0 and task.progress_percent < 100:
        estimated_total = int(elapsed * 100 / task.progress_percent)
        remaining = max(0, estimated_total - elapsed)

    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        progress_percent=task.progress_percent,
        status_message=task.status_message,
        report_content=task.report_content if task.status == "completed" else "",
        error=task.error,
        elapsed_seconds=elapsed,
        remaining_seconds=remaining,
    )


@router.get("/report/{task_id}")
async def download_report(task_id: str):
    """Download generated report as file."""
    from app.services import tasks

    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    if task.status not in ["completed", "partial"] or not task.report_content:
        raise HTTPException(status_code=404, detail="报告未生成")

    safe_topic = sanitize_topic(task.report_content[:50] if task.report_content else "report")
    filename = f"report_{safe_topic}_{datetime.now().strftime('%Y%m%d')}.md"

    content = task.report_content.encode("utf-8") if isinstance(task.report_content, str) else task.report_content

    return FileResponse(
        content,
        media_type="text/markdown",
        filename=filename,
    )


@router.get("/reports", response_model=ReportsListResponse)
async def list_reports():
    """List all generated reports."""
    reports = []
    for f in settings.reports_dir.glob("*.md"):
        stat = f.stat()
        reports.append(
            ReportInfo(
                name=f.name,
                size=stat.st_size,
                created=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                path=str(f),
            )
        )
    reports.sort(key=lambda x: x.created, reverse=True)
    return ReportsListResponse(reports=reports[:20])
