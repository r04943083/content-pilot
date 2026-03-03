# Content Pilot / 内容领航员

AI-driven social media automation tool for Chinese platforms.

[English](#english) | [中文](#chinese)

---

<a id="english"></a>

## English

### Features

- **Multi-platform support**: Xiaohongshu, Douyin, Bilibili, Weibo
- **AI content generation**: Qwen, GLM, OpenAI, Claude — with platform-optimized prompts
- **Web GUI**: Browser-based dashboard for managing accounts, content, publishing, and schedules
- **QR code login**: Scan-to-login for all platforms with session persistence
- **Scheduled publishing**: Cron-based scheduling with optimal posting times
- **Analytics tracking**: Views, likes, comments, follower growth trends
- **Safety controls**: Rate limiting, content validation, human review workflow
- **Anti-detection**: Stealth browser, human-like delays, conservative publishing rates

### Requirements

- Python 3.11+
- An API key: Qwen (阿里千问), GLM (智谱), OpenAI, or Anthropic (Claude)

### Installation

```bash
git clone https://github.com/r04943083/content-pilot.git
cd content-pilot
bash install.sh
```

The install script will automatically:
- Detect Python 3.11+ on your system
- Install `python3-venv` if missing (may ask for sudo password)
- Create a `.venv` virtual environment
- Install all Python dependencies
- Install Playwright Chromium browser and system dependencies
- Create `.env` from template

> **WSL2 / headless Linux users**: If browser launch fails with `libnspr4.so` errors, run:
> ```bash
> sudo playwright install-deps chromium
> ```

After installation, every time you open a new terminal:

```bash
cd content-pilot
source .venv/bin/activate
```

Then edit `.env` to add your API key:

```bash
nano .env
# Default provider is Qwen (千问):
# CP_AI__QWEN_API_KEY=sk-...
#
# Or use GLM (智谱):
# CP_AI__PROVIDER=glm
# CP_AI__GLM_API_KEY=...
#
# Or OpenAI / Claude:
# CP_AI__PROVIDER=openai   CP_AI__OPENAI_API_KEY=sk-...
# CP_AI__PROVIDER=claude   CP_AI__ANTHROPIC_API_KEY=sk-ant-...
```

### Quick Start

```bash
# Step 1 — Login (opens browser, scan QR code with your phone)
content-pilot login --platform xiaohongshu

# Step 2 — Generate content (AI writes a draft, you review it)
#   You'll be prompted to: approve / edit / regenerate / cancel
#   Approved drafts are saved to the local database (not published yet)
content-pilot generate --topic "Python learning tips" --platform xiaohongshu --style tutorial

# Step 3 — Preview before publishing (--dry-run = no actual publish)
content-pilot publish --content-id 1 --dry-run

# Step 4 — Publish for real
content-pilot publish --content-id 1

# Step 5 — Check analytics after publishing
content-pilot analytics summary

# Step 6 (optional) — Set up scheduled auto-generation + publishing
content-pilot schedule add --name "Daily Post" --platform xiaohongshu \
  --topic "Python Tips" --cron "0 20 * * *"
content-pilot run   # start the scheduling daemon

# Or use the Web GUI for a visual interface
content-pilot gui
```

> **Workflow**: `login` → `generate` (AI draft) → `approve` → `publish` (post to platform).
> Generate only creates a local draft. You must run `publish` to actually post it.

### CLI Reference

| Command | Description |
|---------|-------------|
| `login --platform <name\|all>` | Login via QR code |
| `status` | Show all account statuses |
| `generate --topic <t> --platform <p> --style <s>` | Generate AI content |
| `publish --content-id <id> [--dry-run]` | Publish content |
| `schedule add\|list\|remove\|pause\|resume` | Manage schedules |
| `analytics summary\|growth\|post\|export` | View analytics |
| `config show\|validate` | Configuration management |
| `run` | Start scheduling daemon |
| `gui` | Launch web GUI (default: http://127.0.0.1:8080) |

### Content Styles

| Style | Description |
|-------|-------------|
| `tutorial` | Step-by-step guide |
| `review` | Product/service review |
| `lifestyle` | Personal life sharing |
| `knowledge` | Knowledge/educational |
| `story` | Narrative storytelling |

### Configuration

Configuration uses three layers (later overrides earlier):

1. `config/default.toml` - Default settings
2. `~/.content-pilot/config.toml` - User settings
3. Environment variables with `CP_` prefix (e.g., `CP_AI__PROVIDER=openai`)

### Architecture

```
CLI (Click) / Web GUI (NiceGUI)
         ↓
  App Orchestrator → Platform Connectors (Playwright)
         ↓                        ↓
  Content Generator          Browser Manager
  (Qwen/GLM/OpenAI/Claude)  (Stealth + Sessions)
         ↓                        ↓
  Scheduler (APScheduler)    SQLite Database
         ↓
  Safety (Rate Limiter + Validator)
```

---

<a id="chinese"></a>

## 中文

### 功能特性

- **多平台支持**: 小红书、抖音、B站、微博
- **AI 内容生成**: 千问、智谱 GLM、OpenAI、Claude，针对各平台优化的 prompt
- **可视化界面**: 基于浏览器的 Web GUI，管理账号、内容、发布和定时任务
- **扫码登录**: 所有平台支持扫码登录，会话持久化
- **定时发布**: 基于 Cron 的定时调度，内置最佳发布时间建议
- **数据分析**: 浏览、点赞、评论、粉丝增长趋势
- **安全控制**: 频率限制、内容校验、人工审核流程
- **反检测**: 隐身浏览器、仿人延迟、保守发布频率

### 系统要求

- Python 3.11+
- API Key: 千问 (Qwen)、智谱 (GLM)、OpenAI 或 Anthropic (Claude)

### 安装

```bash
git clone https://github.com/r04943083/content-pilot.git
cd content-pilot
bash install.sh
```

安装脚本会自动完成：
- 检测系统 Python 3.11+ 版本
- 缺少 `python3-venv` 时自动安装（可能需要 sudo 密码）
- 创建 `.venv` 虚拟环境
- 安装所有 Python 依赖
- 安装 Playwright Chromium 浏览器及系统依赖
- 从模板创建 `.env` 文件

> **WSL2 / 无桌面 Linux 用户**：如果浏览器启动报错 `libnspr4.so` 找不到，手动运行：
> ```bash
> sudo playwright install-deps chromium
> ```

安装完成后，每次打开新终端需要先激活环境：

```bash
cd content-pilot
source .venv/bin/activate
```

然后编辑 `.env` 填入 API Key：

```bash
nano .env
# 默认使用千问 (Qwen):
# CP_AI__QWEN_API_KEY=sk-...
#
# 或使用智谱 GLM:
# CP_AI__PROVIDER=glm
# CP_AI__GLM_API_KEY=...
#
# 或使用 OpenAI / Claude:
# CP_AI__PROVIDER=openai   CP_AI__OPENAI_API_KEY=sk-...
# CP_AI__PROVIDER=claude   CP_AI__ANTHROPIC_API_KEY=sk-ant-...
```

### 快速上手

```bash
# 第一步 — 登录平台（打开浏览器，用手机扫码）
content-pilot login --platform xiaohongshu

# 第二步 — 生成内容（AI 写草稿，你来审核）
#   会提示你选择: approve(通过) / edit(编辑) / regenerate(重写) / cancel(取消)
#   通过后草稿保存在本地数据库，还没有发布！
content-pilot generate --topic "Python学习技巧" --platform xiaohongshu --style tutorial

# 第三步 — 发布前预览（--dry-run 只看不发）
content-pilot publish --content-id 1 --dry-run

# 第四步 — 正式发布到平台
content-pilot publish --content-id 1

# 第五步 — 发布后查看数据
content-pilot analytics summary

# 第六步（可选）— 设置定时自动生成+发布
content-pilot schedule add --name "每日发帖" --platform xiaohongshu \
  --topic "Python技巧" --cron "0 20 * * *"
content-pilot run   # 启动定时守护进程

# 或者使用可视化界面
content-pilot gui
```

> **完整流程**：`login`(登录) → `generate`(AI生成草稿) → `approve`(审核通过) → `publish`(发布到平台)
> generate 只是在本地生成草稿，必须执行 publish 才会真正发布到平台。

### 内容风格

| 风格 | 说明 |
|------|------|
| `tutorial` | 教程 / 步骤讲解 |
| `review` | 测评 / 产品点评 |
| `lifestyle` | 生活分享 |
| `knowledge` | 知识科普 |
| `story` | 故事叙述 |

### 最佳发布时间

| 平台 | 推荐时段 |
|------|----------|
| 小红书 | 7-9点、12-13点、19-22点 |
| 抖音 | 12-13点、18-20点、21-23点 |
| B站 | 11-13点、17-19点、21-23点 |
| 微博 | 8-9点、12-13点、18-22点 |

### Docker 部署

```bash
# 首次使用需要先在本地登录（需要扫码）
content-pilot login --platform xiaohongshu

# 然后使用 Docker 运行守护进程
docker compose up -d
```

### 常见问题

**Q: `bash install.sh` 提示权限错误？**
安装 `python3-venv` 或 Playwright 系统依赖时需要 sudo 密码，脚本会自动提示。

**Q: `source .venv/bin/activate` 报错 No such file？**
删掉旧的 `.venv` 重新运行 `bash install.sh`：
```bash
rm -rf .venv
bash install.sh
```

**Q: 登录时报错 `TargetClosedError` / `libnspr4.so` 找不到？**
Chromium 缺少系统依赖库，手动安装：
```bash
# 方法一（推荐）：
sudo playwright install-deps chromium

# 方法二（手动）：
sudo apt install -y libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 \
  libgbm1 libpango-1.0-0 libcairo2 libasound2
```
WSL2 用户特别容易遇到此问题，因为 WSL 默认不装 GUI 相关库。

**Q: 如何切换 AI 提供商？**
编辑 `.env`，设置 `CP_AI__PROVIDER=qwen|glm|openai|claude` 并填入对应 API Key。
默认为 `qwen`（千问），推荐国内用户使用千问或 GLM。

### 法律声明

本工具仅供学习和研究用途。使用者需遵守各平台的服务条款和相关法律法规。根据中国《互联网信息服务深度合成管理规定》，AI 生成的内容应当进行标注。请在使用时遵守相关规定。

---

## License

MIT
