"""reply 子命令 — 回复帖子评论"""

import json
import sys

from testpy.api import api_request, require_auth, unwrap


def register(subparsers):
    """向 argparse 注册 reply 子命令"""
    p = subparsers.add_parser("reply", help="回复帖子")

    p.add_argument("post_id", help="帖子 ID")
    p.add_argument("content", nargs="?", default=None, help="回复内容")

    p.add_argument("--list", action="store_true", help="查看该帖子的评论列表")

    return p


def execute(args):
    """路由 reply 子命令"""
    if args.list:
        _list_comments(args)
    elif args.content:
        _post_reply(args)
    else:
        print("错误: 回复必须指定内容，或使用 --list 查看评论")
        sys.exit(1)


def _post_reply(args):
    """发表回复"""
    token, base_url = require_auth()

    body = {"content": args.content}
    resp = api_request(
        "POST",
        f"/forum-posts/{args.post_id}/comments",
        token=token,
        body=body,
        base_url=base_url,
    )
    result = unwrap(resp)

    if result:
        print("回复成功！")
        print(f"  帖子: {args.post_id}")
        print(f"  内容: {args.content}")
    else:
        print("回复失败:", json.dumps(resp, ensure_ascii=False, indent=2))


def _list_comments(args):
    """查看帖子评论"""
    token, base_url = require_auth()

    resp = api_request(
        "GET",
        f"/forum-posts/{args.post_id}/comments",
        token=token,
        base_url=base_url,
    )
    data = unwrap(resp) or {}
    comments = data.get("comments", [])

    if not comments:
        print(f"帖子 {args.post_id} 暂无评论。")
        return

    print(f"帖子 {args.post_id} 共 {len(comments)} 条评论:\n")
    for c in comments:
        author = c.get("author", {}).get("username", "匿名")
        content = c.get("content", "")
        created = (c.get("createdAt") or "")[:16].replace("T", " ")
        likes = c.get("likeCount", 0)
        print(f"  [{author}] {created}  点赞:{likes}")
        print(f"    {content}")
        print()
