"""logout 子命令 — 清除本地 token"""

from testpy.api import delete_token, load_token


def register(subparsers):
    """向 argparse 注册 logout 子命令"""
    return subparsers.add_parser("logout", help="退出登录")


def execute(args):
    """执行 logout 命令"""
    if load_token():
        delete_token()
        print("已退出登录")
    else:
        print("当前未登录")
