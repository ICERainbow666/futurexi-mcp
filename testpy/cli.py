"""
FutureXI CLI 入口
只负责参数解析和子命令路由，具体逻辑在 commands/ 下
"""

import argparse
import os
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中，支持 `python testpy/cli.py` 方式运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Windows 终端 UTF-8 支持
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from testpy.api import DEFAULT_BASE_URL
from testpy.commands import login, profile, set as cmd_set, logout, post, notify, reply

# 子命令注册表: (模块, 命令名)
COMMANDS = [
    (login,   "login"),
    (profile, "profile"),
    (cmd_set, "set"),
    (post,    "post"),
    (reply,   "reply"),
    (notify,  "notify"),
    (logout,  "logout"),
]


def main():
    parser = argparse.ArgumentParser(
        prog="futurexi",
        description="FutureXI CLI - 管理你的 FutureXI 资料",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API 地址 (默认: {DEFAULT_BASE_URL})",
    )
    parser.add_argument("-v", "--version", action="version", version="futurexi 0.1.0")

    sub = parser.add_subparsers(dest="command")

    # 各子命令自行注册参数
    for module, _name in COMMANDS:
        module.register(sub)

    args = parser.parse_args()

    # 路由到对应子命令
    cmd_map = {name: mod.execute for mod, name in COMMANDS}
    handler = cmd_map.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
