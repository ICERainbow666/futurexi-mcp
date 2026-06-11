"""FutureXI MCP Server — 将 CLI 命令暴露为 MCP tools"""

import json
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from testpy.api import (
    api_request,
    load_token,
    save_token,
    delete_token,
    DEFAULT_BASE_URL,
    PROFILE_FIELDS,
    SKILL_FIELDS,
)

mcp = FastMCP("futurexi")

STATUS_MAP = {
    "published": "已发布",
    "pending_review": "待审核",
    "archived": "已归档",
}


def _require_auth() -> tuple[str, str]:
    saved = load_token()
    if not saved:
        raise RuntimeError("未登录，请先调用 login 工具登录")
    return saved["token"], saved.get("base_url", DEFAULT_BASE_URL)


def _safe_request(method: str, path: str, **kwargs) -> dict:
    """包装 api_request，捕获 SystemExit 返回错误 dict 而非杀死进程"""
    try:
        return api_request(method, path, **kwargs)
    except SystemExit as e:
        return {"success": False, "error": str(e)}


def _unwrap(resp: dict):
    if not resp.get("success"):
        return None
    return resp.get("data")


# ── 认证 ────────────────────────────────────────────────

@mcp.tool()
def login(username: str, password: str) -> str:
    """登录 FutureXI 账号，登录后 token 自动保存。"""
    body = {"identifier": username, "password": password}
    resp = _safe_request("POST", "/auth/login", body=body, base_url=DEFAULT_BASE_URL)
    data = resp.get("data", {})
    token = data.get("token") or data.get("access_token")
    if not token:
        return f"登录失败: {json.dumps(resp, ensure_ascii=False)}"
    save_token(token, DEFAULT_BASE_URL)
    return f"登录成功！欢迎 {username}"


@mcp.tool()
def logout() -> str:
    """退出登录，清除本地 token。"""
    delete_token()
    return "已退出登录"


# ── 个人资料 ─────────────────────────────────────────────

@mcp.tool()
def get_profile() -> dict:
    """查看当前用户的个人资料、技能评估和账号信息。"""
    token, base_url = _require_auth()

    user_resp = _safe_request("GET", "/users/me", token=token, base_url=base_url)
    user_data = _unwrap(user_resp) or {}
    user = user_data.get("user") or user_data or {}

    profile_resp = _safe_request("GET", "/player-profiles/me", token=token, base_url=base_url)
    profile = _unwrap(profile_resp) or {}

    return {
        "account": {k: user.get(k) for k in ("username", "email", "role") if k in user},
        "profile": {k: profile.get(k) for k, _, _ in PROFILE_FIELDS},
        "skills": profile.get("skill_scores_json") or {},
    }


@mcp.tool()
def update_profile(
    full_name: str | None = None,
    date_of_birth: str | None = None,
    height: float | None = None,
    weight: float | None = None,
    province_name: str | None = None,
    city_name: str | None = None,
    school_name: str | None = None,
    dominant_foot: str | None = None,
    primary_position: str | None = None,
    team_name: str | None = None,
    jersey_number: int | None = None,
    years_of_experience: int | None = None,
    ball_control: int | None = None,
    passing_accuracy: int | None = None,
    shooting: int | None = None,
    stamina: int | None = None,
    tactical_awareness: int | None = None,
    mental_toughness: int | None = None,
) -> str:
    """修改个人资料或技能评估。只传需要修改的字段，未传的保持不变。"""
    token, base_url = _require_auth()

    existing = {}
    try:
        resp = _safe_request("GET", "/player-profiles/me", token=token, base_url=base_url)
        existing = _unwrap(resp) or {}
    except Exception:
        pass

    payload = {k: existing.get(k) for k, _, _ in PROFILE_FIELDS}

    locals_map = {
        "full_name": full_name, "date_of_birth": date_of_birth,
        "height": height, "weight": weight,
        "province_name": province_name, "city_name": city_name,
        "school_name": school_name, "dominant_foot": dominant_foot,
        "primary_position": primary_position, "team_name": team_name,
        "jersey_number": jersey_number, "years_of_experience": years_of_experience,
    }
    for key, val in locals_map.items():
        if val is not None:
            payload[key] = val

    skills = existing.get("skill_scores_json") or {}
    skills_map = {
        "ball_control": ball_control, "passing_accuracy": passing_accuracy,
        "shooting": shooting, "stamina": stamina,
        "tactical_awareness": tactical_awareness, "mental_toughness": mental_toughness,
    }
    for key, val in skills_map.items():
        if val is not None:
            skills[key] = val
    if skills:
        payload["skill_scores_json"] = skills

    resp = _safe_request("PUT", "/player-profiles/me", token=token, body=payload, base_url=base_url)
    result = _unwrap(resp)
    if result:
        return "资料已保存"
    return f"保存失败: {json.dumps(resp, ensure_ascii=False)}"


# ── 帖子 ────────────────────────────────────────────────

@mcp.tool()
def create_post(
    title: str,
    content: str,
    category: str = "general",
    tags: str | None = None,
) -> dict:
    """发布新帖子。tags 用逗号分隔，例如 '高位压迫,4-3-3'。"""
    token, base_url = _require_auth()

    body = {"title": title, "content": content, "category": category}
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        body["tags"] = tag_list[:6]

    resp = _safe_request("POST", "/forum-posts", token=token, body=body, base_url=base_url)
    result = _unwrap(resp) or {}
    post = result.get("post") or result

    if post:
        return {
            "id": post.get("id"),
            "title": post.get("title"),
            "category": post.get("category"),
            "status": STATUS_MAP.get(post.get("status", ""), post.get("status")),
            "tags": [t.get("label", t) if isinstance(t, dict) else t for t in (post.get("tags") or [])],
        }
    return {"error": json.dumps(resp, ensure_ascii=False)}


@mcp.tool()
def list_posts(status: str = "all") -> list[dict]:
    """查看我的帖子列表。status: all / published / archived。"""
    token, base_url = _require_auth()

    resp = _safe_request("GET", f"/forum-posts/mine?status={status}", token=token, base_url=base_url)
    data = _unwrap(resp) or {}
    posts = data.get("posts", [])

    return [{
        "id": p.get("id"),
        "title": p.get("title"),
        "category": p.get("category"),
        "status": STATUS_MAP.get(p.get("status", ""), p.get("status")),
        "tags": [t.get("label", t) if isinstance(t, dict) else t for t in (p.get("tags") or [])],
    } for p in posts]


@mcp.tool()
def delete_post(post_id: int) -> str:
    """删除指定帖子。"""
    token, base_url = _require_auth()

    resp = _safe_request("DELETE", f"/forum-posts/{post_id}", token=token, base_url=base_url)
    result = _unwrap(resp)
    if result is not None:
        return f"帖子 {post_id} 已删除"
    return f"删除失败: {json.dumps(resp, ensure_ascii=False)}"


# ── 评论 ────────────────────────────────────────────────

@mcp.tool()
def reply_post(post_id: int, content: str) -> str:
    """回复指定帖子。"""
    token, base_url = _require_auth()

    body = {"content": content}
    resp = _safe_request("POST", f"/forum-posts/{post_id}/comments", token=token, body=body, base_url=base_url)
    result = _unwrap(resp)
    if result:
        return f"回复成功，帖子 {post_id}"
    return f"回复失败: {json.dumps(resp, ensure_ascii=False)}"


@mcp.tool()
def list_comments(post_id: int) -> list[dict]:
    """查看指定帖子的评论列表。"""
    token, base_url = _require_auth()

    resp = _safe_request("GET", f"/forum-posts/{post_id}/comments", token=token, base_url=base_url)
    data = _unwrap(resp) or {}
    comments = data.get("comments", [])

    return [{
        "id": c.get("id"),
        "author": c.get("author", {}).get("username", "匿名"),
        "content": c.get("content"),
        "likes": c.get("likeCount", 0),
        "created_at": (c.get("createdAt") or "")[:16].replace("T", " "),
    } for c in comments]


# ── 通知 ────────────────────────────────────────────────

@mcp.tool()
def get_notifications() -> dict:
    """查看通知列表和未读数。"""
    token, base_url = _require_auth()

    resp = _safe_request("GET", "/notifications", token=token, base_url=base_url)
    data = _unwrap(resp) or {}

    return {
        "unread_count": data.get("unreadCount", 0),
        "notifications": [{
            "type": n.get("type"),
            "title": n.get("title"),
            "message": n.get("message"),
            "is_read": n.get("isRead", False),
            "created_at": (n.get("createdAt") or "")[:16].replace("T", " "),
        } for n in data.get("notifications", [])],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
