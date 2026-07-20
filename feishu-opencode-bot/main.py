"""feishu-opencode-bot 主入口。

集成所有组件，实现端到端流程：
  飞书消息 → WebSocket → SecurityGuard（白名单）→ CommandRouter（命令分发）
  → OpencodeClient（API 调用）→ FeishuBot.reply_text/card（回复用户）

启动：
  ./run.sh             # 推荐方式（自动 source .env）
  python main.py       # 直接启动（需先 source .env）

关闭：
  Ctrl+C（SIGINT）
  kill <PID>（SIGTERM）

配置：
  从 config.yaml 加载（${VAR} 自动从环境变量替换）
  依赖 .env 提供：FEISHU_APP_ID/SECRET + OPENCODE_* + FEISHU_WHITELIST_USER_IDS
"""
from __future__ import annotations

import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# 把项目根目录加入 sys.path，便于 `from src.xxx import yyy` 和 `from config import zzz`
sys.path.insert(0, str(Path(__file__).parent))

from config import DEFAULT_CONFIG_PATH, load_config, validate_config
from src.cards import parse_action
from src.commands import CommandRouter
from src.feishu_client import CardActionContext, FeishuBot, MessageContext
from src.opencode_client import OpencodeClient
from src.security import SecurityGuard

logger = logging.getLogger("feishu-opencode-bot")


class BotApp:
    """集成应用：协调 FeishuBot + OpencodeClient + SecurityGuard + CommandRouter。

    职责：
    - 初始化所有组件
    - 处理飞书消息（白名单 → 命令分发 → 回复）
    - 处理卡片按钮回调（解析 action → 命令分发 → 回复）
    - 优雅关闭（signal handling）
    """

    def __init__(self, config: dict) -> None:
        self.config = config

        # 1. 安全：白名单守卫
        security_cfg = config.get("security", {})
        self.security = SecurityGuard(
            allowed_users=security_cfg.get("allowed_users", []),
            allowed_chats=security_cfg.get("allowed_chats", []),
        )

        # 2. opencode 客户端
        opencode_cfg = config["opencode"]
        self.opencode = OpencodeClient(
            base_url=opencode_cfg["base_url"],
            username=opencode_cfg["username"],
            password=opencode_cfg["password"],
        )

        # 3. 命令路由器（自动注册 list/help/status/send/switch_agent/agents）
        self.router = CommandRouter(self.opencode)

        # 4. 飞书 Bot
        feishu_cfg = config["feishu"]
        self.bot = FeishuBot(
            app_id=feishu_cfg["app_id"],
            app_secret=feishu_cfg["app_secret"],
        )
        # 注册 handler
        self.bot.on_message = self._handle_message
        self.bot.on_card_action = self._handle_card_action

        logger.info("BotApp 初始化完成")
        logger.info(
            "  白名单用户数：%d，群白名单数：%d",
            len(self.security.allowed_users),
            len(self.security.allowed_chats),
        )
        logger.info("  opencode: %s", opencode_cfg["base_url"])
        logger.info("  飞书 App ID: %s", feishu_cfg["app_id"])

    async def _handle_message(self, ctx: MessageContext) -> None:
        """处理飞书消息事件。

        流程：
        1. 用户白名单校验（拒绝非白名单用户）
        2. 群聊只响应 @bot（避免噪音）
        3. 只处理文本消息（其他类型提示不支持）
        4. 命令分发（CommandRouter.handle_text）
        5. 回复用户

        Args:
            ctx: 消息上下文
        """
        try:
            # 1. 白名单校验
            if not self.security.is_user_allowed(ctx.user_id):
                logger.warning("拒绝非白名单用户：%s", ctx.user_id)
                # 静默拒绝（不回复，避免信息泄露）
                return

            # 2. 群聊只响应 @bot
            if ctx.chat_type == "group" and not ctx.is_at_bot:
                logger.debug("群消息未 @bot，忽略：%s", ctx.message_id)
                return

            # 3. 只处理文本消息（其他类型暂不支持）
            if ctx.message_type != "text":
                await self.bot.reply_text(
                    ctx,
                    f"⚠️ 暂不支持 {ctx.message_type} 类型消息，仅支持文本命令\n"
                    f"输入 `/help` 查看可用命令",
                )
                return

            # 4. 命令分发
            text = ctx.text.strip()
            if not text:
                return  # 空消息忽略

            logger.info("处理消息 from %s: %s", ctx.user_id, text[:80])
            response = await self.router.handle_text(text)

            # 5. 回复
            if response is None:
                # 不是命令，给帮助提示
                response = (
                    f"❓ 不是命令：`{text[:50]}`\n\n"
                    f"输入 `/help` 查看可用命令"
                )

            await self.bot.reply_text(ctx, response)

        except Exception as e:
            logger.exception("消息处理异常：%s", e)
            try:
                await self.bot.reply_text(
                    ctx,
                    f"❌ 处理消息时出错：{e}\n\n请稍后重试，或输入 /help 查看命令",
                )
            except Exception:
                pass  # 回复也失败，只能记录日志

    async def _handle_card_action(self, ctx: CardActionContext) -> None:
        """处理卡片按钮/select 回调。

        FeishuBot.on_card_action 签名是 ``async (ctx: CardActionContext) -> None``，
        返回值被 SDK 忽略。

        流程：
        1. 白名单校验（卡片回调的 operator）
        2. parse_action 解析 ctx.value → Action
        3. Action.command 传给 CommandRouter
        4. 回复结果（若有 chat_id 可回复则发送）

        Args:
            ctx: 卡片回调上下文（ctx.value 是按钮携带的 dict）
        """
        try:
            # 白名单校验
            if not self.security.is_user_allowed(ctx.operator_open_id):
                logger.warning(
                    "拒绝非白名单用户的卡片回调：%s", ctx.operator_open_id
                )
                return

            action = parse_action(ctx.value)
            if not action.is_valid:
                logger.warning("无效卡片 action：%s", ctx.value)
                return

            logger.info(
                "处理卡片 action：%s → %s", action.action_type, action.command
            )
            response_text = await self.router.handle_text(action.command)

            if response_text is None:
                response_text = "操作完成（无返回内容）"

            # 卡片回调无直接 chat_id；如 action params 携带 chat_id 则发到对应会话
            chat_id = action.params.get("chat_id")
            if chat_id:
                await self.bot.send_text(chat_id, response_text)
            else:
                logger.info("卡片 action 结果（无 chat_id 不主动回复）：%s", response_text[:200])

        except Exception as e:
            logger.exception("卡片回调处理异常：%s", e)

    def run(self) -> int:
        """启动 Bot（阻塞）。

        Returns:
            退出码（0=正常，非 0=错误）
        """
        # signal handling（优雅关闭）
        def shutdown_handler(signum, frame):
            sig_name = signal.Signals(signum).name
            logger.info("收到信号 %s，正在关闭...", sig_name)
            # lark.ws.Client.start() 通常通过抛异常或 sys.exit 退出
            # 这里只记录日志，让 lark 内部处理
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        logger.info("=== 启动 feishu-opencode-bot ===")
        logger.info("Bot 上线，等待飞书消息...")

        try:
            # 启动 WebSocket（阻塞）
            self.bot.start()
        except SystemExit:
            logger.info("Bot 已优雅关闭")
            return 0
        except KeyboardInterrupt:
            logger.info("Bot 被 Ctrl+C 中断")
            return 0
        except Exception as e:
            logger.exception("Bot 启动失败：%s", e)
            return 1

        return 0


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
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
    """主入口。"""
    setup_logging()

    # 加载配置
    try:
        logger.info("加载配置: %s", DEFAULT_CONFIG_PATH)
        config = load_config()
        validate_config(config)
        logger.info("配置校验通过")
    except FileNotFoundError as e:
        logger.error("配置文件缺失：%s", e)
        logger.error("请参考 .env.example 和 config.example.yaml 配置")
        return 1
    except ValueError as e:
        logger.error("配置无效：%s", e)
        return 2
    except Exception as e:
        logger.exception("配置加载异常：%s", e)
        return 3

    # 设置日志级别（按配置）
    log_level = config.get("logging", {}).get("level", "INFO")
    log_file = config.get("logging", {}).get("file")
    if log_level != "INFO" or log_file:
        # 重新配置
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        setup_logging(log_level, log_file)

    # 创建并启动 app
    try:
        app = BotApp(config)
    except Exception as e:
        logger.exception("BotApp 初始化失败：%s", e)
        return 4

    return app.run()


if __name__ == "__main__":
    sys.exit(main())
