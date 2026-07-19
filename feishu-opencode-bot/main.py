"""飞书 Bot 控制 opencode session — 主入口。

Phase 1 Task 1 只实现配置加载和启动占位，
实际 WebSocket 连接和命令分发在后续 Task（3, 5-9）实现。
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# 把项目根目录加入 sys.path，便于 `from src.xxx import yyy`
sys.path.insert(0, str(Path(__file__).parent))

from config import DEFAULT_CONFIG_PATH, load_config, validate_config


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """初始化日志。"""
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def main() -> int:
    """主入口。

    Returns:
        退出码：0=成功，非 0=失败
    """
    logger = logging.getLogger("feishu-opencode-bot")

    try:
        logger.info("加载配置: %s", DEFAULT_CONFIG_PATH)
        config = load_config()
        validate_config(config)
        logger.info("配置校验通过")
    except FileNotFoundError as e:
        logger.error("配置文件缺失: %s", e)
        return 1
    except ValueError as e:
        logger.error("配置无效: %s", e)
        return 2
    except Exception as e:
        logger.exception("配置加载异常: %s", e)
        return 3

    # TODO: Task 3 实现 WebSocket 连接
    # TODO: Task 5-7 实现命令处理
    # TODO: Task 9 实现主循环
    logger.warning(
        "脚手架占位：实际 WebSocket 连接和命令处理在后续 Task 实现"
    )
    logger.info("Phase 1 Task 1 脚手架就绪。")
    return 0


if __name__ == "__main__":
    setup_logging()
    sys.exit(main())