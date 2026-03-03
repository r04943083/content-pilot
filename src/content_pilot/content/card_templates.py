"""HTML/CSS card templates and AI prompts for code-generated images."""

from __future__ import annotations

CARD_STYLES = {
    "quote": {
        "name": "文字引用卡片",
        "description": "大字体居中，渐变背景，适合名言金句",
    },
    "title": {
        "name": "标题封面卡片",
        "description": "标题+副标题布局，适合做封面图",
    },
    "list": {
        "name": "清单卡片",
        "description": "要点列表形式，适合教程/技巧类内容",
    },
    "minimal": {
        "name": "极简卡片",
        "description": "纯文字，干净设计",
    },
}

# Map platform to default card style
DEFAULT_STYLE_MAP = {
    "xiaohongshu": "quote",  # 小红书适合精美引用卡片
    "douyin": "title",       # 抖音适合封面卡片
    "bilibili": "list",      # B站适合清单卡片
    "weibo": "quote",        # 微博适合引用卡片
}

CARD_PROMPT = """你是一个专业的社交媒体视觉设计师。请根据以下内容生成一张配图的 HTML/CSS 代码。

内容标题：{title}
内容摘要：{summary}
关键标签：{tags}
卡片风格：{style_name} - {style_description}

设计要求：
1. 输出完整的 HTML 文件，包含内联 CSS（不要用外部样式表）
2. 固定尺寸：1080x1350 像素（4:5 竖版比例）
3. 使用中文友好字体：system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif
4. 配色要有设计感，避免默认蓝黑配色
5. 适当使用渐变、阴影、圆角等现代设计元素
6. 确保文字清晰可读，对比度足够
7. 内容要完整显示，不要截断

只输出 HTML 代码，从 <!DOCTYPE html> 开始，不要有任何解释或额外文字：
"""

# Fallback HTML template in case AI generation fails
FALLBACK_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            width: 1080px;
            height: 1350px;
            font-family: system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 60px;
            color: white;
        }}
        .container {{
            text-align: center;
            max-width: 900px;
        }}
        h1 {{
            font-size: 64px;
            font-weight: 700;
            line-height: 1.3;
            margin-bottom: 40px;
            text-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }}
        .summary {{
            font-size: 32px;
            line-height: 1.6;
            opacity: 0.95;
            margin-bottom: 50px;
        }}
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            justify-content: center;
        }}
        .tag {{
            background: rgba(255,255,255,0.2);
            padding: 12px 24px;
            border-radius: 30px;
            font-size: 24px;
            backdrop-filter: blur(10px);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p class="summary">{summary}</p>
        <div class="tags">
            {tags_html}
        </div>
    </div>
</body>
</html>
"""


def get_card_prompt(
    title: str,
    summary: str,
    tags: list[str],
    style: str = "quote",
) -> str:
    """Generate the AI prompt for card generation."""
    style_info = CARD_STYLES.get(style, CARD_STYLES["quote"])
    tags_str = ", ".join(f"#{t}" for t in tags) if tags else "无"

    return CARD_PROMPT.format(
        title=title,
        summary=summary[:300] if len(summary) > 300 else summary,
        tags=tags_str,
        style_name=style_info["name"],
        style_description=style_info["description"],
    )


def get_fallback_html(
    title: str,
    summary: str,
    tags: list[str],
) -> str:
    """Generate fallback HTML when AI generation fails."""
    tags_html = "\n".join(
        f'<span class="tag">#{tag}</span>' for tag in tags[:5]
    ) if tags else ""

    return FALLBACK_TEMPLATE.format(
        title=title[:50] if len(title) > 50 else title,
        summary=summary[:200] if len(summary) > 200 else summary,
        tags_html=tags_html,
    )
