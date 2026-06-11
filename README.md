# FutureXI CLI & MCP Server

FutureXI 足球社区的命令行客户端 + MCP Server，支持 CLI 操作和 Claude Code 直接调用。

## 功能

- 登录 / 退出 FutureXI 账号
- 查看 / 修改个人资料和技能评估
- 发布 / 查看 / 删除论坛帖子
- 回复帖子 / 查看评论
- 查看通知

## 安装

```bash
git clone https://github.com/你的用户名/futurexi-mcp.git
cd futurexi-mcp
pip install -e .
```

## 使用方式

### 方式一：CLI 命令行

```bash
# 登录
python testpy/cli.py login <用户名> <密码>

# 查看个人资料
python testpy/cli.py profile

# 修改资料
python testpy/cli.py set --full_name "张三" --height 175

# 发帖
python testpy/cli.py post --title "标题" --content "内容" --category tactics --tags "高位压迫,4-3-3"

# 查看我的帖子
python testpy/cli.py post --list

# 回复帖子
python testpy/cli.py reply <帖子ID> "回复内容"

# 查看评论
python testpy/cli.py reply <帖子ID> --list

# 查看通知
python testpy/cli.py notify

# 退出登录
python testpy/cli.py logout
```

### 方式二：MCP Server（Claude Code）

配置 `~/.claude.json`：

```json
{
  "mcpServers": {
    "futurexi": {
      "command": "python",
      "args": ["-m", "testpy.mcp_server"],
      "cwd": "你的项目路径"
    }
  }
}
```

重启 Claude Code 后，AI 可直接调用以下工具：

| 工具 | 说明 |
|------|------|
| `login` | 登录 FutureXI 账号 |
| `logout` | 退出登录 |
| `get_profile` | 查看个人资料和技能 |
| `update_profile` | 修改个人资料或技能 |
| `create_post` | 发布帖子 |
| `list_posts` | 查看我的帖子 |
| `delete_post` | 删除帖子 |
| `reply_post` | 回复帖子 |
| `list_comments` | 查看帖子评论 |
| `get_notifications` | 查看通知 |

## 项目结构

```
├── testpy/
│   ├── __init__.py
│   ├── api.py           # API 客户端，token 管理
│   ├── cli.py           # CLI 入口
│   ├── mcp_server.py    # MCP Server（10 个 tools）
│   └── commands/
│       ├── login.py
│       ├── profile.py
│       ├── set.py
│       ├── post.py
│       ├── reply.py
│       ├── notify.py
│       └── logout.py
├── pyproject.toml
├── .gitignore
└── README.md
```

## API 地址

默认：`http://127.0.0.1:3100/api/v1`

CLI 可通过 `--base-url` 参数指定其他地址，MCP Server 需修改 `mcp_server.py` 中的 `DEFAULT_BASE_URL`。

## 前置条件

- Python 3.10+
- FutureXI 后端服务运行中

## 依赖

- CLI：无第三方依赖（仅标准库）
- MCP Server：`mcp>=1.0`
