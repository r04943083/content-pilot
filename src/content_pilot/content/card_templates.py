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
配色方案：{color_scheme}

设计要求：
1. 输出完整的 HTML 文件，包含内联 CSS（不要用外部样式表）
2. 固定尺寸：1080x1350 像素（4:5 竖版比例）
3. 使用中文友好字体：system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif
4. 严格按照上面指定的配色方案设计，不要使用其他配色
5. 大量使用渐变、阴影、圆角、装饰图形等现代设计元素
6. 确保文字清晰可读，对比度足够
7. 内容要完整显示，不要截断
8. 每次生成的布局和视觉风格要有变化，避免千篇一律

只输出 HTML 代码，从 <!DOCTYPE html> 开始，不要有任何解释或额外文字：
"""

# Color schemes for variety — rotated per card
CARD_COLOR_SCHEMES = [
    "暖橙落日：#FF6B35 → #F7931E → #FFD23F，白色文字",
    "薄荷清新：#00B09B → #96C93D，白色文字",
    "浪漫粉紫：#E040FB → #7C4DFF → #536DFE，白色文字",
    "深海蓝：#0F2027 → #203A43 → #2C5364，浅蓝/白色文字",
    "蜜桃珊瑚：#FF9A9E → #FECFEF → #FFDDE1，深色文字",
    "森林绿金：#134E5E → #71B280，金色/白色文字",
    "极光紫蓝：#7F00FF → #E100FF，白色文字",
    "暖阳橙红：#FC4A1A → #F7B733，白色文字",
]

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
    page_label: str | None = None,
    color_index: int = 0,
    is_cover: bool = False,
) -> str:
    """Generate the AI prompt for card generation.

    Args:
        title: Card title
        summary: Card summary/content
        tags: List of tags
        style: Card style key
        page_label: Optional page label like "1/4" for multi-card series
        color_index: Index to select a color scheme for variety
        is_cover: If True, generate a cover card with large title
    """
    style_info = CARD_STYLES.get(style, CARD_STYLES["quote"])
    tags_str = ", ".join(f"#{t}" for t in tags) if tags else "无"
    color_scheme = CARD_COLOR_SCHEMES[color_index % len(CARD_COLOR_SCHEMES)]

    prompt = CARD_PROMPT.format(
        title=title,
        summary=summary[:300] if len(summary) > 300 else summary,
        tags=tags_str,
        style_name=style_info["name"],
        style_description=style_info["description"],
        color_scheme=color_scheme,
    )

    if is_cover:
        prompt += (
            "\n重要：这是封面图！请设计为大标题封面卡片："
            "\n- 标题字体要非常大（至少 72px），居中醒目"
            "\n- 不需要显示摘要正文，只显示标题"
            "\n- 可以加装饰性图形、图标或纹理增加视觉冲击力"
            "\n- 整体设计要像杂志封面一样精美吸引人"
        )

    if page_label:
        prompt += f"\n这是系列图第 {page_label} 张，请在卡片标注页码。"

    return prompt


def split_content_for_cards(
    title: str,
    content: str,
    tags: list[str],
    card_count: int,
) -> list[dict]:
    """Split content across multiple cards so each card has different content.

    Args:
        title: Original content title
        content: Full content text
        tags: List of tags
        card_count: Number of cards to generate

    Returns:
        List of dicts with keys: title, summary, tags, page_label
    """
    if card_count <= 1:
        return [{"title": title, "summary": content[:300], "tags": tags, "page_label": None, "is_cover": True}]

    paragraphs = [p.strip() for p in content.split("\n") if p.strip()]

    cards: list[dict] = []

    # Card 1: cover card — big title only, minimal text
    cards.append({
        "title": title,
        "summary": "",
        "tags": [],
        "page_label": f"1/{card_count}",
        "is_cover": True,
    })

    # Middle cards: distribute remaining paragraphs evenly
    remaining = paragraphs[max(1, len(paragraphs) // card_count):]
    middle_count = card_count - 2  # exclude first and last

    if middle_count > 0 and remaining:
        chunk_size = max(1, len(remaining) // (middle_count + 1))
        for i in range(middle_count):
            start = i * chunk_size
            end = start + chunk_size
            chunk = "\n".join(remaining[start:end])
            cards.append({
                "title": title,
                "summary": chunk[:300] if chunk else content[:300],
                "tags": [],
                "page_label": f"{i + 2}/{card_count}",
                "is_cover": False,
            })
        # Last card: remaining paragraphs + tags as CTA
        last_chunk = "\n".join(remaining[middle_count * chunk_size:])
        cards.append({
            "title": title,
            "summary": last_chunk[:300] if last_chunk else content[-300:],
            "tags": tags,
            "page_label": f"{card_count}/{card_count}",
            "is_cover": False,
        })
    else:
        # Only 2 cards total: second card gets the rest + tags
        rest = "\n".join(remaining) if remaining else content[-300:]
        cards.append({
            "title": title,
            "summary": rest[:300],
            "tags": tags,
            "page_label": f"2/{card_count}",
            "is_cover": False,
        })

    return cards


_FALLBACK_GRADIENTS = [
    "linear-gradient(135deg, #FF6B35 0%, #F7931E 50%, #FFD23F 100%)",
    "linear-gradient(135deg, #00B09B 0%, #96C93D 100%)",
    "linear-gradient(135deg, #E040FB 0%, #7C4DFF 50%, #536DFE 100%)",
    "linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%)",
    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "linear-gradient(135deg, #134E5E 0%, #71B280 100%)",
    "linear-gradient(135deg, #7F00FF 0%, #E100FF 100%)",
    "linear-gradient(135deg, #FC4A1A 0%, #F7B733 100%)",
]


def get_fallback_html(
    title: str,
    summary: str,
    tags: list[str],
    color_index: int = 0,
) -> str:
    """Generate fallback HTML when AI generation fails."""
    import random

    tags_html = "\n".join(
        f'<span class="tag">#{tag}</span>' for tag in tags[:5]
    ) if tags else ""

    gradient = _FALLBACK_GRADIENTS[color_index % len(_FALLBACK_GRADIENTS)]

    html = FALLBACK_TEMPLATE.format(
        title=title[:50] if len(title) > 50 else title,
        summary=summary[:200] if len(summary) > 200 else summary,
        tags_html=tags_html,
    )
    # Replace the default gradient with the selected one
    return html.replace(
        "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        gradient,
    )
