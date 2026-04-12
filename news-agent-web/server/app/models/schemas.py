"""Pydantic models for request/response schemas."""

from enum import Enum
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """Supported report types."""

    TREND = "trend"
    COMPARE = "compare"
    COMPREHENSIVE = "comprehensive"
    POLICY = "policy"


class ReportDepth(str, Enum):
    """Report depth levels."""

    SIMPLE = "simple"
    DEPTH = "depth"


class ReportRequest(BaseModel):
    """Request model for report generation."""

    topic: str = Field(..., min_length=1, max_length=100, description="报告主题")
    report_type: ReportType = Field(default=ReportType.TREND, description="报告类型")
    report_depth: ReportDepth = Field(default=ReportDepth.SIMPLE, description="报告深度")
    max_articles: int = Field(default=10, ge=1, le=50, description="最大文章数")


class ReportTypeResponse(BaseModel):
    """Response model for available report types."""

    report_types: dict[str, str]


class TaskStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    status: str
    progress_percent: int
    status_message: str
    report_content: str = ""
    error: str = ""
    elapsed_seconds: int = 0
    remaining_seconds: int = 0


class StopTaskResponse(BaseModel):
    """Response model for stop task action."""

    message: str


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    version: str = "1.0.0"


class ReportInfo(BaseModel):
    """Info model for generated report listing."""

    name: str
    size: int
    created: str
    path: str


class ReportsListResponse(BaseModel):
    """Response model for reports listing."""

    reports: list[ReportInfo]
