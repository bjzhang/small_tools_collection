#!/usr/bin/env bash
# feishu-opencode-bot 启动脚本
#
# 自动 source .env 加载环境变量，然后启动 main.py
#
# 用法：
#   ./run.sh                 # 前台启动
#   ./run.sh --background    # 后台启动（nohup）
#   ./run.sh --check         # 仅检查配置（不启动）

set -euo pipefail

# 切到脚本所在目录
cd "$(dirname "$0")"

# 检查 .env 存在
if [[ ! -f .env ]]; then
    echo "❌ .env 不存在。请：cp .env.example .env，然后填入真实凭据"
    exit 1
fi

# 检查 config.yaml 存在
if [[ ! -f config.yaml ]]; then
    echo "❌ config.yaml 不存在。请参考 config.example.yaml 创建"
    exit 1
fi

# 检查 Python 版本（≥ 3.10）
if ! python3 -c 'import sys; assert sys.version_info >= (3, 10)' 2>/dev/null; then
    echo "❌ Python 版本过低（需要 ≥ 3.10）"
    python3 --version || echo "python3 未安装"
    exit 1
fi

# 优先用 .venv，否则用系统 python
if [[ -d .venv ]]; then
    source .venv/bin/activate
    PYTHON=python
else
    PYTHON=python3
    # 检查依赖
    if ! python3 -c "import httpx, yaml, lark_oapi" 2>/dev/null; then
        echo "⚠️  缺少依赖。请运行：python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
fi

# 加载 .env（自动 export）
set -a
source .env
set +a

# 校验必要的环境变量
for var in FEISHU_APP_ID FEISHU_APP_SECRET OPENCODE_BASE_URL OPENCODE_USERNAME OPENCODE_SERVER_PASSWORD; do
    if [[ -z "${!var:-}" ]]; then
        echo "❌ 环境变量 $var 未设置（请在 .env 中配置）"
        exit 1
    fi
done

# 子命令处理
case "${1:-run}" in
    --check)
        echo "✅ 配置检查通过"
        echo "   - .env 已加载"
        echo "   - config.yaml 存在"
        echo "   - 必要环境变量已设置"
        echo "   - Python: $($PYTHON --version)"
        $PYTHON -c "from config import load_config, validate_config; cfg = load_config(); validate_config(cfg); print('   - config.yaml 校验通过')"
        ;;
    --background)
        echo "🚀 后台启动..."
        nohup $PYTHON main.py > /tmp/feishu-opencode-bot.log 2>&1 &
        echo "   PID: $!"
        echo "   日志: /tmp/feishu-opencode-bot.log"
        echo "   停止: kill $!"
        ;;
    run|"")
        echo "🚀 前台启动 feishu-opencode-bot..."
        echo "   Ctrl+C 退出"
        echo ""
        exec $PYTHON main.py
        ;;
    *)
        echo "用法：./run.sh [--check|--background|run]"
        echo ""
        echo "选项："
        echo "  (无) / run       前台启动"
        echo "  --check          仅检查配置"
        echo "  --background     后台启动（nohup）"
        exit 1
        ;;
esac