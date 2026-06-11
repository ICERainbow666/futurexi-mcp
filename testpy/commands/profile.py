"""profile 子命令 — 查看个人信息中心"""

from testpy.api import (
    api_request,
    require_auth,
    unwrap,
    PROFILE_FIELDS,
    SKILL_FIELDS,
)

ACCOUNT_LABELS = {
    "username": "用户名",
    "email": "邮箱",
    "role": "角色",
    "activityTierKey": "活跃等级",
}


def register(subparsers):
    """向 argparse 注册 profile 子命令"""
    return subparsers.add_parser("profile", help="查看个人信息中心")


def execute(args):
    """执行 profile 命令"""
    token, base_url = require_auth()

    print("=" * 48)
    print("    FutureXI 个人信息中心")
    print("=" * 48)

    # ── 账号信息（只读）──
    user_resp = api_request("GET", "/users/me", token=token, base_url=base_url)
    data = unwrap(user_resp)
    user = (data or {}).get("user") or data or {}

    print("\n【账号信息】(不可更改)")
    if user:
        for key in ("username", "email", "role", "activityTierKey"):
            val = user.get(key)
            if val is not None:
                print(f"  {ACCOUNT_LABELS.get(key, key)}:  {val}")
    else:
        print("  无法获取")

    # ── 玩家档案 ──
    profile_resp = api_request("GET", "/player-profiles/me", token=token, base_url=base_url)
    profile = unwrap(profile_resp)

    print("\n【个人资料】")
    if profile:
        for api_key, label, _ in PROFILE_FIELDS:
            val = profile.get(api_key)
            print(f"  {label}:  {val if val is not None else '未填写'}")

        skills = profile.get("skill_scores_json")
        if skills:
            print("\n【技能评估】")
            for sk, sl in SKILL_FIELDS.items():
                val = skills.get(sk)
                print(f"  {sl}:  {val if val is not None else '未评估'}")
    else:
        print("  暂未创建，用以下命令设置：")
        print("  python testpy/cli.py set --full_name 你的姓名")

    # ── 通知 ──
    try:
        notif_resp = api_request("GET", "/notifications", token=token, base_url=base_url)
        notif_data = unwrap(notif_resp) or {}
        print(f"\n【通知】未读: {notif_data.get('unreadCount', 0)}")
    except SystemExit:
        pass

    # ── 我的帖子 ──
    try:
        posts_resp = api_request("GET", "/forum-posts/mine", token=token, base_url=base_url)
        posts_data = unwrap(posts_resp) or {}
        posts = posts_data.get("posts", [])
        print(f"【我的帖子】共 {len(posts)} 条")
    except SystemExit:
        pass

    print("\n" + "=" * 48)
