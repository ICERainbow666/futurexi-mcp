"""set 子命令 — 修改个人资料"""

import json
import sys

from testpy.api import (
    api_request,
    require_auth,
    unwrap,
    PROFILE_FIELDS,
    SKILL_FIELDS,
)


def register(subparsers):
    """向 argparse 注册 set 子命令"""
    p = subparsers.add_parser("set", help="设置个人资料")

    for api_key, label, field_type in PROFILE_FIELDS:
        if field_type == "choice":
            p.add_argument(f"--{api_key}", choices=["left", "right", "both"], help=label)
        else:
            p.add_argument(f"--{api_key}", help=label)

    # 技能评估（0-100）
    for sk, sl in SKILL_FIELDS.items():
        p.add_argument(f"--{sk}", type=int, choices=range(0, 101), metavar="0-100", help=sl)

    return p


def execute(args):
    """执行 set 命令 — GET 现有档案 → 合并参数 → PUT"""
    token, base_url = require_auth()

    # 获取现有档案（合并用，避免服务端 undefined 问题）
    existing = {}
    try:
        resp = api_request("GET", "/player-profiles/me", token=token, base_url=base_url)
        existing = unwrap(resp) or {}
    except SystemExit:
        pass

    # 用已有数据填充 payload
    payload = {api_key: existing.get(api_key) for api_key, _, _ in PROFILE_FIELDS}

    # 命令行参数覆盖
    for api_key, _, field_type in PROFILE_FIELDS:
        val = getattr(args, api_key, None)
        if val is not None:
            if field_type == "num":
                payload[api_key] = float(val)
            elif field_type == "int":
                payload[api_key] = int(val)
            else:
                payload[api_key] = val

    # 技能评估合并
    existing_skills = existing.get("skill_scores_json") or {}
    skills_changed = False
    for sk in SKILL_FIELDS:
        sv = getattr(args, sk, None)
        if sv is not None:
            existing_skills[sk] = int(sv)
            skills_changed = True

    if skills_changed or existing_skills:
        payload["skill_scores_json"] = existing_skills if existing_skills else None

    # 没有任何指定字段且档案不存在 → 打印帮助
    has_changes = any(getattr(args, k, None) is not None for k, _, _ in PROFILE_FIELDS)
    has_changes = has_changes or skills_changed

    if not has_changes and not existing:
        _print_help()
        return

    resp = api_request("PUT", "/player-profiles/me", token=token, body=payload, base_url=base_url)
    result = unwrap(resp)

    if result:
        print("资料已保存！")
        for api_key, label, _ in PROFILE_FIELDS:
            val = result.get(api_key)
            if val is not None:
                print(f"  {label}:  {val}")
    else:
        print("保存失败:", json.dumps(resp, ensure_ascii=False, indent=2))


def _print_help():
    """打印 set 命令的可用字段列表"""
    print("未指定任何字段。用法示例：")
    print('  python testpy/cli.py set --full_name "张三" --height 175 --weight 70')
    print('  python testpy/cli.py set --dominant_foot right --primary_position "中场"')
    print("\n可用字段：")
    type_hint = {"str": "文本", "num": "数字", "int": "整数", "date": "YYYY-MM-DD", "choice": "left/right/both"}
    for api_key, label, field_type in PROFILE_FIELDS:
        print(f"  --{api_key:25s} {label:10s} ({type_hint[field_type]})")
    print("\n技能评估：")
    for sk, sl in SKILL_FIELDS.items():
        print(f"  --{sk:25s} {sl} (0-100)")
