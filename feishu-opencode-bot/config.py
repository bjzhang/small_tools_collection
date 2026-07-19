"""配置加载：yaml 文件 + 环境变量替换。

加载顺序：
1. 默认值（本文件内）
2. config.yaml（用户填写）
3. 环境变量（最高优先级）

环境变量替换语法：${VAR_NAME}
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.yaml"


def _expand_env_vars(value: Any) -> Any:
    """递归替换字符串中的 ${VAR_NAME} 为环境变量值。

    Args:
        value: 任意配置值（str/dict/list/...）

    Returns:
        替换后的值（未找到的环境变量保持原样或抛错，取决于 strict 模式）
    """
    if isinstance(value, str):
        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                raise ValueError(
                    f"环境变量 {var_name} 未设置（配置中引用了 ${{{var_name}}}）"
                )
            return env_value

        return ENV_VAR_PATTERN.sub(replacer, value)
    if isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(item) for item in value]
    return value


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """加载配置文件并替换环境变量。

    Args:
        config_path: 配置文件路径，默认为项目根目录的 config.yaml

    Returns:
        完整配置字典

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 环境变量未设置
        yaml.YAMLError: YAML 解析失败
    """
    path = config_path or DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"配置文件不存在: {path}\n"
            f"请复制 config.example.yaml 为 config.yaml 并填写凭据"
        )

    with path.open("r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    return _expand_env_vars(raw_config)


def validate_config(config: dict[str, Any]) -> None:
    """校验配置完整性，缺失关键字段时抛错。

    Args:
        config: 已加载的配置

    Raises:
        ValueError: 必填字段缺失
    """
    required_fields = [
        ("feishu", "app_id"),
        ("feishu", "app_secret"),
        ("opencode", "base_url"),
        ("opencode", "username"),
        ("opencode", "password"),
    ]
    for section, key in required_fields:
        if section not in config:
            raise ValueError(f"配置缺少 [{section}] 段")
        if key not in config[section] or not config[section][key]:
            raise ValueError(f"配置 [{section}].{key} 必填且不能为空")

    if (
        "security" not in config
        or "allowed_users" not in config["security"]
        or not config["security"]["allowed_users"]
    ):
        raise ValueError(
            "配置 [security].allowed_users 必填（至少 1 个飞书 user open_id）"
        )


# 测试/调试入口
if __name__ == "__main__":
    import json

    cfg = load_config()
    validate_config(cfg)
    # 打印脱敏后的配置（凭据显示为 ***）
    safe = cfg.copy()
    safe["feishu"] = {**safe["feishu"], "app_secret": "***"}
    safe["opencode"] = {**safe["opencode"], "password": "***"}
    print(json.dumps(safe, indent=2, ensure_ascii=False))