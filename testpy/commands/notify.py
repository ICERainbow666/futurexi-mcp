"""notify 子命令 — 查看通知"""

from testpy.api import api_request, require_auth, unwrap


def register(subparsers):
    """向 argparse 注册 notify 子命令"""
    p = subparsers.add_parser("notify", help="查看通知")
    p.add_argument("--unread", action="store_true", help="仅显示未读通知")
    return p


def execute(args):
    """执行 notify 命令"""
    token, base_url = require_auth()

    resp = api_request("GET", "/notifications", token=token, base_url=base_url)
    data = unwrap(resp) or {}

    unread = data.get("unreadCount", 0)
    notifications = data.get("notifications", [])

    print(f"未读通知: {unread}\n")

    if not notifications:
        print("暂无通知。")
        return

    for n in notifications:
        is_read = n.get("isRead", False)
        mark = "  " if is_read else "[新]"
        ntype = n.get("type", "")
        title = n.get("title", "")
        message = n.get("message", "")
        created = (n.get("createdAt") or "")[:16].replace("T", " ")

        print(f"  {mark} [{ntype}] {title}")
        if message:
            print(f"       {message}")
        print(f"       {created}")
        print()
