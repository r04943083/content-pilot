"""Prompt templates for different platforms and content styles."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"

# Built-in templates (used if TOML files don't exist)
_BUILTIN = {
    "xiaohongshu": {
        "system": (
            "你是一位小红书爆款内容创作者。你的内容风格：使用emoji、分点列表、"
            "语气亲切自然、标题吸引人、适当使用关键词。"
            "内容长度控制在500-800字。"
        ),
        "styles": {
            "tutorial": "写一篇小红书教程笔记，主题是：{topic}\n要求：分步骤讲解，配合emoji，口语化。",
            "review": "写一篇小红书测评笔记，主题是：{topic}\n要求：真实体验感，优缺点分析，推荐指数。",
            "lifestyle": "写一篇小红书生活分享笔记，主题是：{topic}\n要求：有故事感，引发共鸣，分享心得。",
            "knowledge": "写一篇小红书知识科普笔记，主题是：{topic}\n要求：通俗易懂，干货满满，适合收藏。",
            "story": "写一篇小红书故事笔记，主题是：{topic}\n要求：有起承转合，引人入胜，有情感共鸣。",
        },
    },
    "douyin": {
        "system": (
            "你是一位抖音短视频文案创作者。你的风格：开头用hook抓住注意力、"
            "语言简洁有力、适合口播或字幕展示、节奏快。"
            "文案长度控制在200-400字。"
        ),
        "styles": {
            "tutorial": "写一段抖音教程视频文案，主题是：{topic}\n要求：开头用问题hook，分段简洁，适合1分钟视频。",
            "review": "写一段抖音测评视频文案，主题是：{topic}\n要求：直入主题，简洁评价，结尾引导互动。",
            "lifestyle": "写一段抖音生活vlog文案，主题是：{topic}\n要求：画面感强，生活气息，配合BGM节奏。",
            "knowledge": "写一段抖音知识类视频文案，主题是：{topic}\n要求：颠覆认知的开头，信息密度高，结尾总结。",
            "story": "写一段抖音故事类视频文案，主题是：{topic}\n要求：悬念开头，节奏紧凑，反转结尾。",
        },
    },
    "bilibili": {
        "system": (
            "你是一位B站UP主级别的内容创作者。你的风格：深度长文、"
            "逻辑清晰、有专业度、适当幽默、引经据典。"
            "内容长度控制在800-2000字。"
        ),
        "styles": {
            "tutorial": "写一篇B站专栏教程文章，主题是：{topic}\n要求：系统性讲解，代码示例（如适用），深度分析。",
            "review": "写一篇B站专栏测评文章，主题是：{topic}\n要求：详细对比，数据支撑，客观分析。",
            "lifestyle": "写一篇B站专栏生活分享，主题是：{topic}\n要求：有深度思考，不浮于表面。",
            "knowledge": "写一篇B站专栏知识文章，主题是：{topic}\n要求：深度科普，引用来源，逻辑严密。",
            "story": "写一篇B站专栏故事文章，主题是：{topic}\n要求：叙事完整，文笔流畅，引人深思。",
        },
    },
    "weibo": {
        "system": (
            "你是一位微博热门内容创作者。你的风格：简短有力、话题性强、"
            "适当使用话题标签、引发讨论和转发。"
            "内容长度控制在200-500字。"
        ),
        "styles": {
            "tutorial": "写一条微博教程帖子，主题是：{topic}\n要求：简洁实用，适合快速阅读，加话题标签。",
            "review": "写一条微博测评帖子，主题是：{topic}\n要求：一句话总结+详细点评，引导互动。",
            "lifestyle": "写一条微博生活分享帖子，主题是：{topic}\n要求：有态度，引发共鸣，适合转发。",
            "knowledge": "写一条微博知识科普帖子，主题是：{topic}\n要求：颠覆常识，信息量大，适合收藏。",
            "story": "写一条微博故事帖子，主题是：{topic}\n要求：短小精悍，有冲击力，引发讨论。",
        },
    },
}

_OUTPUT_FORMAT = """

请严格按以下格式输出：
标题: <标题内容>
<正文内容>
标签: #标签1 #标签2 #标签3
"""


@lru_cache
def _load_toml_prompts(platform: str) -> dict | None:
    path = _PROMPTS_DIR / f"{platform}.toml"
    if path.exists():
        with open(path, "rb") as f:
            return tomllib.load(f)
    return None


def get_prompt(platform: str, style: str, topic: str, word_count: str | None = None) -> str:
    """Build the full prompt for content generation.

    Args:
        platform: Target platform
        style: Content style
        topic: Content topic
        word_count: Optional word count key (short/standard/long) to override platform defaults
    """
    # Try TOML file first
    toml_data = _load_toml_prompts(platform)
    if toml_data:
        system = toml_data.get("system", "")
        template = toml_data.get("styles", {}).get(style, "")
        if template:
            prompt = f"{system}\n\n{template.format(topic=topic)}{_OUTPUT_FORMAT}"
            return _append_word_count(prompt, word_count)

    # Fall back to built-in
    builtin = _BUILTIN.get(platform)
    if not builtin:
        prompt = f"Write social media content about: {topic}{_OUTPUT_FORMAT}"
        return _append_word_count(prompt, word_count)

    system = builtin["system"]
    template = builtin["styles"].get(style, builtin["styles"]["tutorial"])
    prompt = f"{system}\n\n{template.format(topic=topic)}{_OUTPUT_FORMAT}"
    return _append_word_count(prompt, word_count)


def _append_word_count(prompt: str, word_count: str | None) -> str:
    """Append word count instruction to prompt if specified."""
    if not word_count:
        return prompt

    from content_pilot.constants import WORD_COUNT_OPTIONS
    option = WORD_COUNT_OPTIONS.get(word_count)
    if option:
        prompt += f"\n内容长度要求：{option['range']}字"
    return prompt
