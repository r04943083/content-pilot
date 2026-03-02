# Content Pilot / 内容领航员

AI-driven social media automation tool for Chinese platforms.

[English](#english) | [中文](#chinese)

---

<a id="english"></a>

## English

### Features

- **Multi-platform support**: Xiaohongshu, Douyin, Bilibili, Weibo
- **AI content generation**: Claude API & OpenAI API with platform-optimized prompts
- **QR code login**: Scan-to-login for all platforms with session persistence
- **Scheduled publishing**: Cron-based scheduling with optimal posting times
- **Analytics tracking**: Views, likes, comments, follower growth trends
- **Safety controls**: Rate limiting, content validation, human review workflow
- **Anti-detection**: Stealth browser, human-like delays, conservative publishing rates

### Installation

```bash
# Clone and install (one command)
git clone https://github.com/r04943083/content-pilot.git
cd content-pilot
bash install.sh
source .venv/bin/activate

# Edit .env with your API keys
nano .env
```

### Quick Start

```bash
# 1. Login to a platform
content-pilot login --platform xiaohongshu

# 2. Generate content
content-pilot generate --topic "Python learning tips" --platform xiaohongshu --style tutorial

# 3. Publish
content-pilot publish --content-id 1

# 4. Check analytics
content-pilot analytics summary

# 5. Set up scheduled publishing
content-pilot schedule add --name "Daily Post" --platform xiaohongshu \
  --topic "Python Tips" --cron "0 20 * * *"

# 6. Start the daemon
content-pilot run
```

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

### Configuration

Configuration uses three layers (later overrides earlier):

1. `config/default.toml` - Default settings
2. `~/.content-pilot/config.toml` - User settings
3. Environment variables with `CP_` prefix (e.g., `CP_AI__PROVIDER=openai`)

### Architecture

```
CLI (Click) → App Orchestrator → Platform Connectors (Playwright)
                ↓                        ↓
         Content Generator          Browser Manager
         (Claude/OpenAI)            (Stealth + Sessions)
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
- **AI 内容生成**: Claude API 和 OpenAI API，针对各平台优化的 prompt
- **扫码登录**: 所有平台支持扫码登录，会话持久化
- **定时发布**: 基于 Cron 的定时调度，内置最佳发布时间建议
- **数据分析**: 浏览、点赞、评论、粉丝增长趋势
- **安全控制**: 频率限制、内容校验、人工审核流程
- **反检测**: 隐身浏览器、仿人延迟、保守发布频率

### 安装

```bash
# 克隆并一键安装
git clone https://github.com/r04943083/content-pilot.git
cd content-pilot
bash install.sh
source .venv/bin/activate

# 编辑 .env 填入 API key
nano .env
```

### 快速上手

```bash
# 1. 登录平台
content-pilot login --platform xiaohongshu

# 2. 生成内容
content-pilot generate --topic "Python学习技巧" --platform xiaohongshu --style tutorial

# 3. 发布
content-pilot publish --content-id 1

# 4. 查看数据
content-pilot analytics summary

# 5. 设置定时发布
content-pilot schedule add --name "每日发帖" --platform xiaohongshu \
  --topic "Python技巧" --cron "0 20 * * *"

# 6. 启动守护进程
content-pilot run
```

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

### 法律声明

本工具仅供学习和研究用途。使用者需遵守各平台的服务条款和相关法律法规。根据中国《互联网信息服务深度合成管理规定》，AI 生成的内容应当进行标注。请在使用时遵守相关规定。

---

## License

MIT
