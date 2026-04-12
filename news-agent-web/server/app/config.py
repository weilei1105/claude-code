"""Configuration management using environment variables."""

import os
from pathlib import Path


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Claude Code CLI configuration
        self.claude_code_dir: str = os.environ.get(
            "CLAUDE_CODE_PATH", "C:/Users/Administrator/claude-code"
        )
        self.claude_cli: str = os.path.join(self.claude_code_dir, "dist", "cli.js")

        # Server configuration
        self.server_host: str = os.environ.get("SERVER_HOST", "0.0.0.0")
        self.server_port: int = int(os.environ.get("SERVER_PORT", "8000"))

        # Runtime paths
        self.bun_path: str = os.environ.get("BUN_PATH", "bun")
        self.reports_dir: Path = Path(os.environ.get("REPORTS_DIR", "generated_reports"))

        # Process pool configuration
        self.process_pool_size: int = int(os.environ.get("PROCESS_POOL_SIZE", "2"))

        # Timeouts (seconds)
        self.simple_timeout: int = int(os.environ.get("SIMPLE_TIMEOUT", "300"))
        self.depth_timeout: int = int(os.environ.get("DEPTH_TIMEOUT", "900"))
        self.heartbeat_interval: int = int(os.environ.get("HEARTBEAT_INTERVAL", "15"))

        # CORS settings
        self.cors_origins: list = ["*"]

        # Ensure reports directory exists
        self.reports_dir.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()
