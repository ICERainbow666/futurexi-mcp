"""post 子命令 — 发帖、查看帖子列表、删除帖子"""

import json
import sys

from testpy.api import api_request, require_auth, unwrap

STATUS_MAP = {
    "published": "已发布",
    "pending_review": "待审核",
    "archived": "已归档",
}


def register(subparsers):
    """向 argparse 注册 post 子命令"""
    p = subparsers.add_parser("post", help="管理论坛帖子")

    group = p.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true", help="查看我的帖子列表")
    group.add_argument("--delete", metavar="ID", help="删除指定帖子")

    p.add_argument("--status", default="all",
                   choices=["published", "archived", "all"],
                   help="列表筛选状态 (默认: all)")

    p.add_argument("--title", help="帖子标题")
    p.add_argument("--content", help="帖子内容")
    p.add_argument("--category", default="general",
                   choices=["training", "tactics", "equipment", "matches", "general"],
                   help="帖子分类 (默认: general)")
    p.add_argument("--tags", help="标签，逗号分隔 (例如: 高位压迫,肋部穿插)")

    return p


def execute(args):
    """路由 post 子命令"""
    if args.list:
        _list_posts(args)
    elif args.delete:
        _delete_post(args)
    elif args.title or args.content:
        _create_post(args)
    else:
        _list_posts(args)


def _create_post(args):
    """创建新帖子"""
    if not args.title:
        print("错误: 发帖必须指定 --title")
        sys.exit(1)
    if not args.content:
        print("错误: 发帖必须指定 --content")
        sys.exit(1)

    token, base_url = require_auth()

    body = {
        "title": args.title,
        "content": args.content,
        "category": args.category,
    }

    if args.tags:
        tag_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        body["tags"] = tag_list[:6]

    resp = api_request("POST", "/forum-posts", token=token, body=body, base_url=base_url)
    result = unwrap(resp) or {}
    post = result.get("post") or result

    if post:
        print("发帖成功！")
        print(f"  ID:     {post.get('id', '未知')}")
        print(f"  标题:   {post.get('title', args.title)}")
        print(f"  分类:   {post.get('category', args.category)}")
        status = post.get("status")
        if status:
            print(f"  状态:   {STATUS_MAP.get(status, status)}")
        tags_raw = post.get("tags") or []
        if tags_raw:
            tags = ", ".join(t.get("label", str(t)) if isinstance(t, dict) else str(t) for t in tags_raw)
            print(f"  标签:   {tags}")
    else:
        print("发帖失败:", json.dumps(resp, ensure_ascii=False, indent=2))


def _list_posts(args):
    """列出我的帖子"""
    token, base_url = require_auth()

    resp = api_request("GET", f"/forum-posts/mine?status={args.status}", token=token, base_url=base_url)
    data = unwrap(resp) or {}
    posts = data.get("posts", [])

    if not posts:
        print("暂无帖子。")
        return

    print(f"共 {len(posts)} 条帖子:\n")
    print(f"  {'ID':<6} {'状态':<16} {'分类':<10} {'标签':<20} {'标题'}")
    print(f"  {'-'*6} {'-'*16} {'-'*10} {'-'*20} {'-'*30}")
    for p in posts:
        pid = p.get("id", "?")
        title = p.get("title", "无标题")
        category = p.get("category", "-")
        status = STATUS_MAP.get(p.get("status", ""), p.get("status", "-"))
        tags_raw = p.get("tags") or []
        tags = ", ".join(t.get("label", str(t)) if isinstance(t, dict) else str(t) for t in tags_raw)
        print(f"  {str(pid):<6} {status:<16} {category:<10} {tags:<20} {title}")


def _delete_post(args):
    """删除指定帖子"""
    token, base_url = require_auth()

    resp = api_request("DELETE", f"/forum-posts/{args.delete}", token=token, base_url=base_url)
    result = unwrap(resp)

    if result is not None:
        print(f"帖子 {args.delete} 已删除。")
    else:
        print("删除失败:", json.dumps(resp, ensure_ascii=False, indent=2))
