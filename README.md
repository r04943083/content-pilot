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

### Quick Start (GUI)

After installation, every time you open a new terminal:

```bash
cd content-pilot
source .venv/bin/activate
content-pilot gui
```

Then open http://127.0.0.1:8080 in your browser.

#### Step-by-Step Workflow

1. **Configure API Key** — Go to **Settings** page, select your AI provider and enter the API key
2. **Login to Platforms** — Go to **Accounts** page, click login button for each platform and scan QR code with your phone
3. **Generate Content** — Go to **Content** page, enter a topic, select platform and style, click **Generate**
4. **Review & Edit** — Preview the AI-generated content, edit if needed, then approve
5. **Publish** — Go to **Publish** page, select approved drafts and click **Publish**
6. **Schedule (Optional)** — Go to **Schedule** page to set up automated daily posting

### GUI Pages Overview

| Page | Description |
|------|-------------|
| **Dashboard** | Overview of accounts and recent posts |
| **Accounts** | Scan QR code to login to each platform |
| **Content** | Generate AI content, preview and edit drafts |
| **Publish** | Manage and publish approved drafts |
| **Schedule** | Set up automated posting schedules |
| **Settings** | Configure AI provider and API keys |

### Content Styles

| Style | Description |
|-------|-------------|
| `tutorial` | Step-by-step guide |
| `review` | Product/service review |
| `lifestyle` | Personal life sharing |
| `knowledge` | Knowledge/educational |
| `story` | Narrative storytelling |

### Best Posting Times

| Platform | Recommended Times |
|----------|-------------------|
| Xiaohongshu | 7-9am, 12-1pm, 7-10pm |
| Douyin | 12-1pm, 6-8pm, 9-11pm |
| Bilibili | 11am-1pm, 5-7pm, 9-11pm |
| Weibo | 8-9am, 12-1pm, 6-10pm |

### Configuration

Configuration uses three layers (later overrides earlier):

1. `config/default.toml` - Default settings
2. `~/.content-pilot/config.toml` - User settings
3. Environment variables with `CP_` prefix (e.g., `CP_AI__PROVIDER=openai`)

You can configure everything via the **Settings** page in the GUI, or manually edit `.env`:

```bash
# Default provider is Qwen (千问):
CP_AI__QWEN_API_KEY=sk-...

# Or use GLM (智谱):
CP_AI__PROVIDER=glm
CP_AI__GLM_API_KEY=...

# Or OpenAI / Claude:
CP_AI__PROVIDER=openai   CP_AI__OPENAI_API_KEY=sk-...
CP_AI__PROVIDER=claude   CP_AI__ANTHROPIC_API_KEY=sk-ant-...
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

### 快速上手（GUI）

安装完成后，每次打开新终端需要先激活环境：

```bash
cd content-pilot
source .venv/bin/activate
content-pilot gui
```

然后在浏览器中打开 http://127.0.0.1:8080

#### 操作流程

1. **配置 API Key** — 进入 **Settings** 页面，选择 AI 提供商并输入 API Key
2. **登录平台** — 进入 **Accounts** 页面，点击各平台的登录按钮，用手机扫码
3. **生成内容** — 进入 **Content** 页面，输入主题，选择平台和风格，点击 **Generate**
4. **审核编辑** — 预览 AI 生成的内容，按需编辑，然后批准
5. **发布** — 进入 **Publish** 页面，选择已批准的草稿，点击 **Publish**
6. **定时任务（可选）** — 进入 **Schedule** 页面设置每日自动发帖

### GUI 页面说明

| 页面 | 功能 |
|------|------|
| **Dashboard** | 账号和最近帖子概览 |
| **Accounts** | 各平台扫码登录 |
| **Content** | AI 内容生成、预览和编辑 |
| **Publish** | 管理和发布已批准的草稿 |
| **Schedule** | 设置定时发布任务 |
| **Settings** | 配置 AI 提供商和 API Keys |

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

### 配置

配置使用三层结构（后者覆盖前者）：

1. `config/default.toml` - 默认设置
2. `~/.content-pilot/config.toml` - 用户设置
3. 环境变量，前缀为 `CP_`（如 `CP_AI__PROVIDER=openai`）

你可以在 GUI 的 **Settings** 页面配置一切，或者手动编辑 `.env`：

```bash
# 默认使用千问 (Qwen):
CP_AI__QWEN_API_KEY=sk-...

# 或使用智谱 GLM:
CP_AI__PROVIDER=glm
CP_AI__GLM_API_KEY=...

# 或使用 OpenAI / Claude:
CP_AI__PROVIDER=openai   CP_AI__OPENAI_API_KEY=sk-...
CP_AI__PROVIDER=claude   CP_AI__ANTHROPIC_API_KEY=sk-ant-...
```

---

## CLI Reference (Advanced)

For users who prefer command-line interface:

```bash
# Login via QR code
content-pilot login --platform xiaohongshu

# Check account status
content-pilot status

# Generate content
content-pilot generate --topic "Python学习技巧" --platform xiaohongshu --style tutorial

# Publish (dry-run first)
content-pilot publish --content-id 1 --dry-run
content-pilot publish --content-id 1

# Analytics
content-pilot analytics summary

# Schedule management
content-pilot schedule add --name "每日发帖" --platform xiaohongshu --topic "Python技巧" --cron "0 20 * * *"
content-pilot schedule list
content-pilot run   # start daemon
```

---

## Docker Deployment

```bash
# First login locally (requires QR scan)
content-pilot login --platform xiaohongshu

# Then run daemon with Docker
docker compose up -d
```

---

## FAQ

**Q: `bash install.sh` shows permission error?**
Installing `python3-venv` or Playwright system dependencies requires sudo password. The script will prompt automatically.

**Q: `source .venv/bin/activate` reports No such file?**
Delete the old `.venv` and run `bash install.sh` again:
```bash
rm -rf .venv
bash install.sh
```

**Q: Login reports `TargetClosedError` / `libnspr4.so` not found?**
Chromium is missing system dependencies. Install them:
```bash
sudo playwright install-deps chromium
```

**Q: How to switch AI provider?**
Edit `.env` and set `CP_AI__PROVIDER=qwen|glm|openai|claude` with the corresponding API key.
Default is `qwen` (千问), recommended for users in China.

---

## Legal Disclaimer

This tool is for learning and research purposes only. Users must comply with the terms of service of each platform and relevant laws and regulations. According to China's "Provisions on the Administration of Deep Synthesis of Internet Information Services", AI-generated content should be labeled. Please comply with relevant regulations when using.

---

## License

MIT
