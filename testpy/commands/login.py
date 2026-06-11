"""login 子命令 — 登录 FutureXI 并缓存 token"""

import json
import sys

from testpy.api import api_request, save_token


def register(subparsers):
    """向 argparse 注册 login 子命令"""
    p = subparsers.add_parser("login", help="登录 FutureXI")
    p.add_argument("username", help="用户名或邮箱")
    p.add_argument("password", help="密码")
    return p


def execute(args):
    """执行 login 命令"""
    body = {"identifier": args.username, "password": args.password}
    resp = api_request("POST", "/auth/login", body=body, base_url=args.base_url)
    data = resp.get("data", {})
    token = data.get("token") or data.get("access_token")

    if not token:
        print("登录失败，未返回 token")
        print("响应:", json.dumps(resp, ensure_ascii=False, indent=2))
        sys.exit(1)

    save_token(token, args.base_url)
    print(f"登录成功！欢迎 {args.username}")
