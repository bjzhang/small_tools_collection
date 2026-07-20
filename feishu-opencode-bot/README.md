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

## 快速开始

### 1. 配置准备

```bash
cd tools_collections/feishu-opencode-bot/

# 复制环境变量模板（敏感凭据，已 gitignore）
cp .env.example .env
# 编辑 .env，填入真实凭据：
#   - FEISHU_APP_ID / FEISHU_APP_SECRET（飞书企业自建应用）
#   - OPENCODE_BASE_URL / OPENCODE_USERNAME / OPENCODE_SERVER_PASSWORD
#   - FEISHU_WHITELIST_USER_IDS（逗号分隔，仅作参考）

# 复制配置模板（运行时配置，已 gitignore）
cp config.example.yaml config.yaml
# 编辑 config.yaml：
#   - 所有 ${VAR} 自动从 .env 加载（无需修改）
#   - security.allowed_users 必须填入你的 user open_id（YAML list，不能从 .env 自动读取）
```

### 2. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 启动

```bash
./run.sh              # 前台启动
./run.sh --check      # 仅检查配置
./run.sh --background # 后台启动（nohup）
```

run.sh 会自动 `source .env` 加载环境变量，校验配置，然后启动 main.py。

### 4. 字段名约定

⚠️ **OPENCODE_SERVER_PASSWORD**（带 `SERVER_`）：与 opencode 官方约定一致。
启动 `opencode serve` 时使用相同的环境变量名，确保密码同步：

```bash
# 终端 1：启动 opencode serve
export OPENCODE_SERVER_PASSWORD='your-password'
opencode serve --port 4096

# 终端 2：启动 feishu-opencode-bot
cd tools_collections/feishu-opencode-bot/
./run.sh  # 自动从 .env 读取 OPENCODE_SERVER_PASSWORD
```

## 配置文件

`config.yaml`（gitignore 保护，不入仓）：
- `feishu.app_id` / `feishu.app_secret`：飞书应用凭据
- `opencode.base_url` / `opencode.username` / `opencode.password`：opencode serve
- `security.allowed_users`：飞书 user open_id 白名单
- `security.allowed_chats`：飞书 chat_id 群白名单（可选）

环境变量替换语法：`${VAR_NAME}`（如 `${OPENCODE_SERVER_PASSWORD}`）