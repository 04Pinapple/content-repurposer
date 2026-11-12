#!/usr/bin/env python3
"""把一篇原始素材一键改写成多平台文案。

用法：
    python repurpose.py -i examples/sample_article.md            # 调用模型
    python repurpose.py -i examples/sample_article.md --mock     # 离线示例，不花钱
    python repurpose.py -i article.md -p xiaohongshu --dry-run   # 只看 prompt
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from prompts import DEFAULT_PLATFORMS, PLATFORMS, build_prompt


def load_article(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"找不到输入文件：{path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(f"输入文件是空的：{path}")
    return text


def extract_title(article: str) -> str:
    for line in article.splitlines():
        if line.strip().startswith("#"):
            return line.strip().lstrip("#").strip()
    first_line = next((line.strip() for line in article.splitlines() if line.strip()), "")
    return first_line[:24] or "未命名素材"


def body_paragraphs(article: str) -> list[str]:
    blocks = re.split(r"\n\s*\n", article)
    return [
        block.strip()
        for block in blocks
        if block.strip() and not block.strip().startswith("#")
    ]


def to_plain_line(block: str) -> str:
    """把一段 Markdown 压成一行纯文本，去掉引用和列表标记。"""
    joined = " ".join(part.strip() for part in block.splitlines() if part.strip())
    return joined.lstrip(">#-* ").strip()


def clip(text: str, limit: int = 60) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def mock_output(platform: str, article: str, tone: str) -> str:
    """离线生成结构正确的示例稿，用来验证流程和做演示，不调用任何模型。"""
    spec = PLATFORMS[platform]
    title = extract_title(article)
    points = body_paragraphs(article)[:3] or [title]
    first_lines = [clip(to_plain_line(paragraph)) for paragraph in points]

    header = f"<!-- 离线示例输出（--mock），未调用模型，仅用于验证结构。平台：{spec['label']} -->\n"

    if platform == "xiaohongshu":
        body = "\n\n".join(
            f"{i}. {line}" for i, line in enumerate(first_lines, start=1)
        )
        return (
            f"{header}# {title[:18]}\n\n"
            f"先说结论：{first_lines[0]}\n\n"
            f"{body}\n\n"
            f"你在这件事上踩过什么坑？评论区聊聊。\n\n"
            "#内容运营 #AI工具 #效率提升"
        )

    if platform == "wechat":
        sections = "\n\n".join(
            f"## {i}. {line[:20]}\n\n{line}" for i, line in enumerate(first_lines, start=1)
        )
        return (
            f"{header}# {title}\n\n"
            f"如果你也在做内容，大概率遇到过同一个问题：一篇东西写完，还要按平台再改三遍。\n\n"
            f"{sections}\n\n"
            f"一句话带走：流程能被拆成规则的部分，就值得交给工具。"
        )

    if platform == "weibo":
        return (
            f"{header}{first_lines[0]}\n\n"
            f"{first_lines[1] if len(first_lines) > 1 else '这件事没有想象中复杂。'}\n\n"
            f"#内容创作#"
        )

    storyboard = "\n\n".join(
        f"镜号 {i}｜口播：{line}｜画面：字幕板 + 关键词高亮"
        for i, line in enumerate(first_lines, start=1)
    )
    return (
        f"{header}[钩子] 你以为改稿最花时间？其实最花时间的是重复判断。\n\n"
        f"{storyboard}\n\n"
        f"镜号 {len(first_lines) + 1}｜口播：把规则写清楚，剩下的交给工具。｜画面：结尾卡"
    )


def call_llm(prompt: str, model: str, base_url: str | None, api_key: str | None) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        raise SystemExit("缺少依赖，先运行：pip install -r requirements.txt")

    if not api_key:
        raise SystemExit(
            "没有找到 API Key。请设置环境变量 OPENAI_API_KEY，"
            "或用 --mock 先在离线模式下试跑。"
        )

    client = OpenAI(api_key=api_key, base_url=base_url or None)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    return (response.choices[0].message.content or "").strip()


def parse_platforms(raw: str) -> list[str]:
    names = [name.strip().lower() for name in raw.split(",") if name.strip()]
    unknown = [name for name in names if name not in PLATFORMS]
    if unknown:
        raise SystemExit(
            f"不支持的平台：{', '.join(unknown)}。可选：{', '.join(PLATFORMS)}"
        )
    if not names:
        raise SystemExit("至少选择一个平台。")
    return names


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="把一篇原始素材改写成多平台文案")
    parser.add_argument("-i", "--input", required=True, help="原始素材文件（Markdown 或纯文本）")
    parser.add_argument(
        "-p",
        "--platforms",
        default=",".join(DEFAULT_PLATFORMS),
        help=f"目标平台，逗号分隔。可选：{', '.join(PLATFORMS)}",
    )
    parser.add_argument("-t", "--tone", default="真诚、克制、有信息量", help="语气要求")
    parser.add_argument("-b", "--brand", default="", help="账号人设或品牌语气说明")
    parser.add_argument("-o", "--out", default="output", help="输出目录")
    parser.add_argument("--model", default=os.getenv("MODEL", "gpt-4o-mini"), help="模型名称")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENAI_BASE_URL"),
        help="OpenAI 兼容接口地址，例如 DeepSeek、Moonshot、智谱的 endpoint",
    )
    parser.add_argument("--dry-run", action="store_true", help="只打印 prompt，不调用模型")
    parser.add_argument(
        "--mock", action="store_true", help="离线生成示例稿，不调用模型、不需要 API Key"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    platforms = parse_platforms(args.platforms)
    article = load_article(Path(args.input))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv("OPENAI_API_KEY")
    results: list[tuple[str, str]] = []

    for platform in platforms:
        prompt = build_prompt(platform, article, args.tone, args.brand)
        label = PLATFORMS[platform]["label"]

        if args.dry_run:
            print(f"===== {label} prompt =====\n{prompt}")
            continue

        if args.mock:
            content = mock_output(platform, article, args.tone)
        else:
            print(f"[{label}] 调用模型中……", file=sys.stderr)
            content = call_llm(prompt, args.model, args.base_url, api_key)

        target = out_dir / f"{platform}.md"
        target.write_text(content + "\n", encoding="utf-8")
        results.append((label, target))
        print(f"[{label}] 已写入 {target}")

    if results:
        combined = out_dir / "all.md"
        parts = [
            f"# {label}\n\n{target.read_text(encoding='utf-8')}"
            for label, target in results
        ]
        combined.write_text("\n\n---\n\n".join(parts), encoding="utf-8")
        print(f"合并稿：{combined}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
