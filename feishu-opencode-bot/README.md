# feishu-opencode-bot

飞书 Bot 控制 opencode session（Phase 1）。

## 状态

🚧 **脚手架阶段（Task 1 / 10 已完成）**

后续任务：
- Task 2: opencode HTTP API 客户端
- Task 3: 飞书 WebSocket 连接
- Task 4: 用户白名单
- Task 5-7: 4 个核心命令（/list, /status, /send, /switch_agent）
- Task 8: 交互式卡片
- Task 9: 集成 + main 主循环
- Task 10: 测试 + 文档

## 前置资源

参见 `.sisyphus/drafts/T217-prerequisites-manual.md`。

启动前需准备：
1. opencode serve 运行中（默认 http://127.0.0.1:4096）
2. 飞书 App ID/Secret（注册企业自建应用）
3. 飞书 user_id（白名单）

## 快速开始（脚手架阶段）

```bash
cd tools_collections/feishu-opencode-bot/

# 安装依赖
pip install -r requirements.txt

# 复制配置模板
cp config.example.yaml config.yaml
# 编辑 config.yaml 填入凭据

# 设置环境变量
export OPENCODE_SERVER_PASSWORD='your-password'

# 运行（当前只会校验配置并退出）
python main.py
```

## 配置文件

`config.yaml`（gitignore 保护，不入仓）：
- `feishu.app_id` / `feishu.app_secret`：飞书应用凭据
- `opencode.base_url` / `opencode.username` / `opencode.password`：opencode serve
- `security.allowed_users`：飞书 user open_id 白名单
- `security.allowed_chats`：飞书 chat_id 群白名单（可选）

环境变量替换语法：`${VAR_NAME}`（如 `${OPENCODE_SERVER_PASSWORD}`）