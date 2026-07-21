# feishu-opencode-bot

通过飞书 Bot 远程控制 [opencode](https://github.com/sst/opencode) session —— 在飞书里查看/切换 agent、发送指令、查看会话状态，无需 SSH 到开发机。

## 状态

✅ **全部完成（10/10）**

| Task | 内容 | 状态 |
|------|------|------|
| 1 | 项目脚手架 + 配置加载 | ✅ |
| 2 | opencode HTTP API 客户端（`src/opencode_client.py`） | ✅ |
| 3 | 飞书 WebSocket 长连接（`src/feishu_client.py`，wss://msg-frontier.feishu.cn） | ✅ |
| 4 | 用户白名单 SecurityGuard（`src/security.py`） | ✅ |
| 5 | `/list` + `/help` 命令 | ✅ |
| 6 | `/status` + `/send` 命令 | ✅ |
| 7 | `/switch_agent` + `/agents` 命令 | ✅ |
| 8 | 交互式卡片（`src/cards.py`） | ✅ |
| 9 | 集成 + main 主循环（`main.py`） | ✅ |
| 10 | 测试 + 文档（`tests/` + 本 README） | ✅ |

---

## 功能介绍

feishu-opencode-bot 是一个桥接 **飞书 IM** 与 **opencode serve** 的远程控制机器人。它通过飞书官方 WebSocket 长连接（无需公网回调 URL）接收用户私聊或群 @ 消息，解析为命令后调用 opencode HTTP API，再把结果回复到飞书。

### 核心能力

- 📋 **会话管理**：列出所有 opencode session，查看会话详情与最近消息历史
- 💬 **远程下发指令**：在飞书里向指定 session 发送自然语言消息（触发 agent 执行）
- 🔀 **切换 Agent**：远程把一个 session 切换到不同 agent（prometheus / atlas / sisyphus 等），切换前自动校验 agent 是否在可用列表中
- 🤖 **Agent 发现**：列出 opencode 实例上所有可用 agent 及其描述、模型
- 🃏 **交互式卡片**：会话列表、会话详情、agent 选择均以飞书互动卡片呈现，点按钮即可操作
- 🔐 **白名单安全**：只有 `config.yaml` 中配置的 `allowed_users` / `allowed_chats` 才能操作；非白名单用户静默忽略
- 🔁 **自动重连**：基于 `lark.ws.Client` 的 `auto_reconnect=True`，飞书长连接断开后自动恢复

### 架构一览

```
飞书用户 IM
     │  (wss://msg-frontier.feishu.cn)
     ▼
FeishuBot (src/feishu_client.py)        ← lark-oapi WebSocket 长连接
     │  MessageContext / CardActionContext
     ▼
SecurityGuard (src/security.py)         ← 用户/群白名单 + 输入清理
     │
     ▼
CommandRouter (src/commands.py)         ← /list /status /send /switch_agent /agents /help
     │
     ▼
OpencodeClient (src/opencode_client.py) ← httpx → opencode serve HTTP API
     │
     ▼
opencode serve (默认 http://127.0.0.1:4096)
```

卡片渲染由 `src/cards.py` 负责，包含 `build_session_list_card` / `build_session_detail_card` / `build_agent_selection_card` / `build_simple_card` / `build_error_card` 等构造器。

---

## 前置条件

### 1. opencode serve 运行中

feishu-opencode-bot 不内嵌 opencode，需要一个独立的 `opencode serve` 实例作为后端。

```bash
# 默认监听 http://127.0.0.1:4096
export OPENCODE_SERVER_PASSWORD='your-strong-password'
opencode serve --port 4096
```

要求：
- opencode serve 可达（默认 `http://127.0.0.1:4096`，可改 `OPENCODE_BASE_URL`）
- 已知 `username`（默认 `opencode`）和 `OPENCODE_SERVER_PASSWORD`
- 至少存在 1 个 session（否则 `/list` 返回 "📭 当前没有 opencode session"）
- `~/.config/opencode/` 下已配置好可用 agent（否则 `/agents` 为空）

### 2. 飞书企业自建应用

前往 [飞书开放平台](https://open.feishu.cn/app) 创建一个 **企业自建应用**，获取：

- **App ID**（形如 `cli_xxxxxxxxxxxxxxxx`）
- **App Secret**（形如 `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

应用需开通以下权限（"权限管理" → 添加权限）：
- `im:message`（接收并读取用户消息）
- `im:message:send_as_bot`（以机器人身份发送消息）
- `im:chat`（获取群信息，群 @ 场景需要）
- `card:action:trigger`（接收卡片按钮回调）

并在 **"事件与回调"** 页：
- 启用 **长连接模式**（WebSocket）—— 本项目不使用公网回调 URL
- 订阅事件 **`im.message.receive_v1`**（接收消息）
- 订阅回调 **`card.action.trigger`**（卡片按钮）

把机器人在 **"应用功能 → 机器人"** 中启用，并把它拉入要使用的私聊或群聊。

### 3. 飞书 user open_id（白名单）

机器人只服务白名单用户。你需要拿到自己的飞书 `open_id`（形如 `ou_xxxxxxxxxxxxxxxx`），填入 `config.yaml` 的 `security.allowed_users`。

获取方式：
- 调用飞书开放接口 `/contact/v3/users` 查询
- 或先发一条消息给机器人，从日志 `收到消息 [...] from ou_xxx:` 中复制

### 4. 运行环境

- Python ≥ 3.10（`run.sh` 会自动检查）
- 依赖见 `requirements.txt`：`httpx` / `pyyaml` / `lark-oapi`（即 `lark_oapi`）

---

## 配置说明

项目用 **两份配置**，均已被 `.gitignore` 保护，不会入仓：

| 文件 | 用途 | 模板 |
|------|------|------|
| `.env` | 敏感凭据（App Secret、opencode 密码） | `.env.example` |
| `config.yaml` | 运行时配置（含白名单） | `config.example.yaml` |

### `.env` 字段

| 变量 | 必填 | 说明 |
|------|:----:|------|
| `FEISHU_APP_ID` | ✅ | 飞书企业自建应用 App ID |
| `FEISHU_APP_SECRET` | ✅ | 飞书企业自建应用 App Secret |
| `OPENCODE_BASE_URL` | ✅ | opencode serve 地址（默认 `http://127.0.0.1:4096`） |
| `OPENCODE_USERNAME` | ✅ | opencode serve 用户名（默认 `opencode`） |
| `OPENCODE_SERVER_PASSWORD` | ✅ | opencode serve 密码（与启动 `opencode serve` 时同名同值） |
| `FEISHU_WHITELIST_USER_IDS` | ❌ | 逗号分隔的 open_id，仅作记录参考；**实际生效的白名单在 `config.yaml`** |

> ⚠️ **字段名约定**：`OPENCODE_SERVER_PASSWORD`（带 `SERVER_`）与 opencode 官方约定一致。启动 `opencode serve` 时使用相同环境变量名，确保密码同步。

### `config.yaml` 字段

```yaml
feishu:
  app_id: "${FEISHU_APP_ID}"            # 从 .env 自动替换
  app_secret: "${FEISHU_APP_SECRET}"

opencode:
  base_url: "${OPENCODE_BASE_URL}"
  username: "${OPENCODE_USERNAME}"
  password: "${OPENCODE_SERVER_PASSWORD}"

security:
  allowed_users:                        # 必填，至少 1 个飞书 open_id（YAML list，不能从 .env 自动读取）
    - "ou_xxxxxxxxxxxxxxxx"
  allowed_chats:                        # 可选，群白名单 chat_id
    - "oc_xxxxxxxxxxxxxxxx"

logging:
  level: "INFO"                         # DEBUG / INFO / WARNING / ERROR
  file: null                            # null=stdout，或指定文件路径
```

### 环境变量替换语法

`config.yaml` 中任何 `${VAR_NAME}` 占位符都会在加载时（`config.py: _expand_env_vars`）被同名环境变量替换。找不到的环境变量会直接抛 `ValueError`，避免运行时凭据为空。

⚠️ **重要**：`security.allowed_users` 是 YAML list，不能写成 `${VAR}` —— 必须显式列出每个 open_id。

### 配置加载优先级

1. 默认值（`config.py` 内）
2. `config.yaml`（用户填写）
3. 环境变量（`${VAR}` 替换，最高优先级）

---

## 启动命令

### 推荐：`run.sh`

`run.sh` 会自动 `source .env`、校验必要环境变量、检查 Python 版本与依赖，然后启动 `main.py`。

```bash
cd tools_collections/feishu-opencode-bot/

./run.sh              # 前台启动（Ctrl+C 退出）
./run.sh --check      # 仅检查配置（不启动）
./run.sh --background # 后台启动（nohup，日志写 /tmp/feishu-opencode-bot.log）
```

`run.sh` 做的事：
1. 检查 `.env` 和 `config.yaml` 存在
2. 检查 Python ≥ 3.10
3. 优先使用 `.venv`，否则校验系统 python 的依赖（`httpx` / `yaml` / `lark_oapi`）
4. `set -a; source .env; set +a` 加载环境变量
5. 校验 `FEISHU_APP_ID` / `FEISHU_APP_SECRET` / `OPENCODE_BASE_URL` / `OPENCODE_USERNAME` / `OPENCODE_SERVER_PASSWORD` 五个必填变量
6. 启动 `main.py`

### 首次安装

```bash
cd tools_collections/feishu-opencode-bot/

# 1. 配置文件
cp .env.example .env
# 编辑 .env，填入真实凭据
cp config.example.yaml config.yaml
# 编辑 config.yaml，至少填入 security.allowed_users

# 2. 依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 校验 + 启动
./run.sh --check
./run.sh
```

### 手动启动（不推荐）

如果跳过 `run.sh`，需自行 `export` 环境变量：

```bash
set -a; source .env; set +a
python main.py
```

### 端到端启动流程（opencode + bot）

```bash
# 终端 1：启动 opencode serve
export OPENCODE_SERVER_PASSWORD='your-password'
opencode serve --port 4096

# 终端 2：启动 feishu-opencode-bot
cd tools_collections/feishu-opencode-bot/
./run.sh  # 自动从 .env 读取 OPENCODE_SERVER_PASSWORD
```

### 停止

- 前台：`Ctrl+C`（SIGINT）
- 后台：`kill <PID>`（`run.sh --background` 会打印 PID；或 `pgrep -f "python main.py"`）

---

## 命令列表

所有命令以 `/` 开头，大小写不敏感，空格分隔参数（Phase 1 不支持引号、转义、管道）。非命令文本会提示 "不是命令"。

| 命令 | 参数 | 说明 |
|------|------|------|
| `/list` | — | 列出所有 opencode session（id / agent / title） |
| `/status <session_id> [N]` | session_id 必填；N 可选，默认 5，范围 0–50 | 查看 session 详情 + 最近 N 条消息 |
| `/send <session_id> <message>` | session_id + 任意消息文本 | 向 session 发送消息（触发 agent 执行） |
| `/switch_agent <session_id> <agent>` | session_id + agent 名（大小写不敏感） | 切换 session 的 agent（自动校验是否在可用列表） |
| `/agents` | — | 列出 opencode 实例所有可用 agent 及描述、模型 |
| `/help` | — | 显示所有已注册命令及示例 |

### 使用示例

```
/list
/status ses_abc123
/status ses_abc123 10
/send ses_abc123 重启服务并验证健康检查
/switch_agent ses_abc123 prometheus
/agents
/help
```

### 安全说明

- `/send` 的消息内容会经过 `SecurityGuard.sanitize_input()` 清理（剥离危险字符）
- `/switch_agent` 必须先 `list_agents()` 校验 agent 名在可用列表中，不允许任意字符串（防注入）
- session 不存在时返回 `❌ Session ses_xxx 不存在`，并提示 `/list`
- 所有命令异常都会被 `CommandRouter.dispatch` 捕获，回复 `❌ 命令执行失败：...`，不会让 bot 崩溃

### 交互式卡片

`/list`、`/status`、`/agents` 等命令除了文本响应，还会通过 `src/cards.py` 构造飞书互动卡片：
- **会话列表卡片**：每个 session 一个按钮，点击直达详情
- **会话详情卡片**：含 "发送消息" / "切换 agent" 等快捷按钮
- **Agent 选择卡片**：列出可切换的 agent，点击即执行 `/switch_agent`
- **错误卡片**：统一的错误展示样式

卡片回调由 `FeishuBot.on_card_action` → `BotApp._handle_card_action` 处理，同样经过白名单校验。

---

## 故障排查

### 启动类

**❌ `.env 不存在`**
```
cp .env.example .env  # 然后填入真实凭据
```

**❌ `config.yaml 不存在`**
```
cp config.example.yaml config.yaml  # 至少填入 security.allowed_users
```

**❌ `环境变量 XXX 未设置（请在 .env 中配置）`**
检查 `.env` 是否包含全部 5 个必填变量：`FEISHU_APP_ID` / `FEISHU_APP_SECRET` / `OPENCODE_BASE_URL` / `OPENCODE_USERNAME` / `OPENCODE_SERVER_PASSWORD`。

**❌ `Python 版本过低（需要 ≥ 3.10）`**
升级 Python，或用 `pyenv` / `conda` 安装 3.10+。

**❌ `缺少依赖。请运行：python3 -m venv .venv && ...`**
按提示创建虚拟环境并 `pip install -r requirements.txt`；或直接 `source .venv/bin/activate` 后再 `./run.sh`。

**❌ `环境变量 VAR_NAME 未设置（配置中引用了 ${VAR_NAME}）`**
`config.yaml` 引用了 `.env` 里没有的变量。检查 `.env` 是否覆盖了 `config.yaml` 中所有 `${...}` 占位符。

### 运行时类

**机器人不响应任何消息**
1. 确认发送者 `open_id` 已在 `config.yaml: security.allowed_users`（非白名单用户会被 **静默忽略**，无错误日志）
2. 群聊里必须 @ 机器人（`is_at_bot == True` 才处理）
3. 查看日志是否有 `收到消息 [...]` 行 —— 没有说明飞书长连接未建立，检查 App ID/Secret 与事件订阅配置

**`❌ 获取 session 列表失败：...`**
opencode serve 不可达或鉴权失败：
- 确认 `opencode serve` 正在运行：`curl http://127.0.0.1:4096/health`
- 确认 `.env` 的 `OPENCODE_SERVER_PASSWORD` 与启动 `opencode serve` 时一致
- 确认 `OPENCODE_BASE_URL` 正确（远端时改成本机可访问的地址）

**`❌ Session ses_xxx 不存在`**
session 已被删除或 id 错误。重新 `/list` 查看当前可用 session。

**`❌ 无效 agent：xxx`**
agent 名不在 opencode 可用列表中。用 `/agents` 查看完整列表；agent 名大小写不敏感但必须完全匹配 `id`。

**`📭 当前没有可用 agent（检查 opencode serve 配置）`**
`~/.config/opencode/` 下没有配置任何 agent。检查 opencode 本身的 agent 配置。

**`WebSocket 已断开` 日志反复出现**
- 检查网络/代理是否能出网到 `wss://msg-frontier.feishu.cn`
- 检查 App Secret 是否正确（鉴权失败会导致连接被踢）
- `lark.ws.Client` 内置 `auto_reconnect=True`，临时网络抖动会自动恢复；持续断开需排查上述两项

**后台进程日志在哪**
`./run.sh --background` 的日志默认写到 `/tmp/feishu-opencode-bot.log`。前台启动则直接打印到 stdout。

### 诊断步骤

1. `./run.sh --check` —— 先确认配置无误
2. 前台启动 `./run.sh`，观察启动日志：
   - `BotApp 初始化完成` → 组件装配成功
   - `WebSocket 连接中...` → 正在建立飞书长连接
3. 私聊机器人发送 `/help`，应有响应
4. 若无响应：检查白名单、@ 机器人、App 事件订阅是否齐全

---

## 项目结构

```
feishu-opencode-bot/
├── main.py                  # 主入口（BotApp 集成所有组件）
├── config.py                # 配置加载 + ${VAR} 替换 + 校验
├── run.sh                   # 启动脚本（自动 source .env）
├── requirements.txt
├── .env.example             # 敏感凭据模板
├── config.example.yaml      # 运行时配置模板
├── src/
│   ├── feishu_client.py     # 飞书 WebSocket 长连接 + 消息/卡片回调
│   ├── opencode_client.py   # opencode HTTP API 客户端
│   ├── commands.py          # 命令解析 + 路由 + 6 个内置 handler
│   ├── cards.py             # 交互式卡片构造器
│   ├── security.py          # 白名单 + 输入清理
│   ├── exceptions.py        # opencode 异常层级
│   └── types.py             # Session/Agent/Message TypedDict
└── tests/                   # pytest 单元测试（test_main/feishu_client/cards/commands/security/opencode_client）
```

---

## 参考

- 前置资源详情：`.sisyphus/drafts/T217-prerequisites-manual.md`
- 任务计划：`.sisyphus/plans/T217-feishu-opencode-bot.md`
- [opencode](https://github.com/sst/opencode) / [lark-oapi (Python)](https://github.com/larksuite/oapi-sdk-python)
