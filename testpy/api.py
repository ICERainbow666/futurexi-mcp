"""
FutureXI API 客户端
负责 HTTP 请求、token 管理、通用数据结构定义
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ── 常量 ──────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent   # Testcli/
CONFIG_DIR = PROJECT_ROOT / ".futurexi"
TOKEN_FILE = CONFIG_DIR / "token.json"
DEFAULT_BASE_URL = "http://127.0.0.1:3100/api/v1"

# 玩家档案字段: (api_key, 中文名, 类型)
PROFILE_FIELDS = [
    ("full_name",           "姓名",        "str"),
    ("date_of_birth",       "出生日期",    "date"),
    ("height",              "身高(cm)",    "num"),
    ("weight",              "体重(kg)",    "num"),
    ("province_name",       "省份",        "str"),
    ("city_name",           "城市",        "str"),
    ("school_name",         "学校",        "str"),
    ("dominant_foot",       "惯用脚",      "choice"),
    ("primary_position",    "主要位置",    "str"),
    ("team_name",           "球队名称",    "str"),
    ("jersey_number",       "球衣号码",    "int"),
    ("years_of_experience", "训练年限",    "int"),
]

SKILL_FIELDS = {
    "ball_control":         "控球",
    "passing_accuracy":     "传球",
    "shooting":             "射门",
    "stamina":              "体能",
    "tactical_awareness":   "战术意识",
    "mental_toughness":     "心理韧性",
}

# ── Token 管理 ────────────────────────────────────────

def save_token(token: str, base_url: str):
    """将登录 token 保存到本地文件"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(
        json.dumps({"token": token, "base_url": base_url}),
        encoding="utf-8",
    )


def load_token() -> dict | None:
    """读取本地缓存的 token，不存在或损坏返回 None"""
    if not TOKEN_FILE.exists():
        return None
    try:
        return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def delete_token():
    """删除本地 token 文件"""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def require_auth() -> tuple[str, str]:
    """获取已登录的 token 和 base_url，未登录则退出"""
    saved = load_token()
    if not saved:
        print("未登录，请先执行: python testpy/cli.py login <用户名> <密码>")
        sys.exit(1)
    return saved["token"], saved.get("base_url", DEFAULT_BASE_URL)


# ── HTTP 请求 ─────────────────────────────────────────

def unwrap(resp: dict):
    """从 API 标准响应中提取 data 字段"""
    if not resp.get("success"):
        return None
    return resp.get("data")


def api_request(
    method: str,
    path: str,
    token: str | None = None,
    body: dict | None = None,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    """发送 HTTP 请求并返回 JSON 响应，失败时打印错误并退出"""
    url = f"{base_url.rstrip('/')}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        try:
            err = json.loads(err_body)
        except json.JSONDecodeError:
            err = {"message": err_body}

        if e.code == 401:
            msg = err.get("error", {}).get("message", "") or err.get("message", "")
            if "expired" in msg.lower() or "invalid" in msg.lower():
                print("登录已过期，请重新登录:")
                print("  python testpy/cli.py login <用户名> <密码>")
                sys.exit(1)

        print(f"HTTP {e.code}: {err.get('message', err_body)}")
        if err.get("details"):
            for field, msg in err["details"].items():
                print(f"  {field}: {msg}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"连接失败: {e.reason}")
        sys.exit(1)
