#!/usr/bin/env python3
"""
learn-OpenClaw HTML 生成脚本
将所有 Markdown 课程和面试材料合并为一个美观的 HTML 文件。

依赖安装：
  pip install markdown

使用方式：
  python scripts/build-html.py
"""

import os
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    print("Installing markdown...")
    os.system(f"{sys.executable} -m pip install markdown")
    import markdown

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SECTIONS = {
    "课程内容": [
        ("第一阶段：基础认知", [
            "lessons/01-what-is-ai-agent.md",
            "lessons/02-agent-core-concepts.md",
            "lessons/03-what-is-openclaw.md",
            "lessons/04-install-openclaw.md",
            "lessons/05-first-conversation.md",
        ]),
        ("第二阶段：核心架构", [
            "lessons/06-gateway-architecture.md",
            "lessons/07-agent-runner.md",
            "lessons/08-react-loop.md",
            "lessons/09-context-window.md",
            "lessons/10-memory-system.md",
        ]),
        ("第三阶段：进阶实战", [
            "lessons/11-skills-system.md",
            "lessons/12-mcp-protocol.md",
            "lessons/13-multi-channel.md",
            "lessons/14-plugin-development.md",
            "lessons/15-automation-workflow.md",
        ]),
        ("第四阶段：面试冲刺", [
            "lessons/16-security-governance.md",
            "lessons/17-source-code-tour.md",
            "lessons/18-system-design.md",
            "lessons/19-resume-guide.md",
            "lessons/20-mock-interview.md",
        ]),
    ],
    "面试专区": [
        ("八股文大全", ["interview/baguweng.md"]),
        ("面试题库", ["interview/questions.md"]),
        ("STAR面试稿", ["interview/star-interview-scripts.md"]),
        ("简历模板", ["interview/resume-template.md"]),
        ("简历撰写指南", ["interview/resume-writing-guide.md"]),
        ("项目介绍话术", ["interview/project-introduction.md"]),
        ("面试官视角", ["interview/interviewer-perspective.md"]),
        ("岗位市场分析", ["interview/job-market-2026.md"]),
    ],
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>learn-OpenClaw - 面试导向完全学习指南</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
                         'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            line-height: 1.8;
            color: #333;
            background: #f5f5f5;
        }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 20px;
            text-align: center;
            margin-bottom: 30px;
            border-radius: 0 0 20px 20px;
        }}
        header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        header p {{ font-size: 1.2em; opacity: 0.9; }}
        nav {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        nav h2 {{ color: #667eea; margin-bottom: 15px; }}
        nav ul {{ list-style: none; padding-left: 0; }}
        nav li {{ padding: 5px 0; }}
        nav a {{ color: #333; text-decoration: none; }}
        nav a:hover {{ color: #667eea; }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .section h1 {{ color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
        .section h2 {{ color: #764ba2; margin: 25px 0 15px; }}
        .section h3 {{ color: #333; margin: 20px 0 10px; }}
        .section h4 {{ color: #555; margin: 15px 0 8px; }}
        code {{
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SFMono-Regular', Consolas, monospace;
            font-size: 0.9em;
        }}
        pre {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
        }}
        pre code {{ background: none; color: inherit; padding: 0; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{ background: #f8f8f8; font-weight: 600; }}
        blockquote {{
            border-left: 4px solid #667eea;
            padding: 10px 20px;
            margin: 15px 0;
            background: #f8f9ff;
            border-radius: 0 8px 8px 0;
        }}
        img {{ max-width: 100%; height: auto; border-radius: 8px; margin: 15px 0; }}
        details {{ margin: 10px 0; }}
        summary {{ cursor: pointer; font-weight: 600; color: #667eea; }}
        footer {{
            text-align: center;
            padding: 30px;
            color: #999;
        }}
        @media print {{
            body {{ background: white; }}
            .section {{ box-shadow: none; page-break-inside: avoid; }}
            header {{ background: #667eea !important; -webkit-print-color-adjust: exact; }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>learn-OpenClaw</h1>
        <p>面试导向完全学习指南 | 20节课 + 110道八股文 + STAR面试稿 + 简历模板</p>
    </header>
    <div class="container">
        <nav>
            <h2>目录导航</h2>
            {toc}
        </nav>
        {content}
    </div>
    <footer>
        <p>learn-OpenClaw | Made with care for every job seeker in 2026</p>
        <p><a href="https://github.com/bcefghj/learn-OpenClaw">GitHub</a></p>
    </footer>
</body>
</html>"""


def read_md(filepath: str) -> str:
    path = PROJECT_ROOT / filepath
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"*File not found: {filepath}*"


def md_to_html(md_text: str) -> str:
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "codehilite", "toc"],
    )


def build_toc(sections: dict) -> str:
    toc_parts = []
    for section_name, subsections in sections.items():
        toc_parts.append(f"<h3>{section_name}</h3><ul>")
        for sub_name, _ in subsections:
            anchor = sub_name.replace(" ", "-").replace("：", "-")
            toc_parts.append(f'<li><a href="#{anchor}">{sub_name}</a></li>')
        toc_parts.append("</ul>")
    return "\n".join(toc_parts)


def build_content(sections: dict) -> str:
    content_parts = []
    for section_name, subsections in sections.items():
        content_parts.append(f'<div class="section"><h1>{section_name}</h1>')
        for sub_name, files in subsections:
            anchor = sub_name.replace(" ", "-").replace("：", "-")
            content_parts.append(f'<h2 id="{anchor}">{sub_name}</h2>')
            for f in files:
                md_text = read_md(f)
                html = md_to_html(md_text)
                content_parts.append(html)
        content_parts.append("</div>")
    return "\n".join(content_parts)


def main():
    output_dir = PROJECT_ROOT / "docs"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "index.html"

    toc = build_toc(SECTIONS)
    content = build_content(SECTIONS)
    html = HTML_TEMPLATE.format(toc=toc, content=content)

    output_path.write_text(html, encoding="utf-8")
    print(f"HTML generated: {output_path}")
    print(f"Open in browser: file://{output_path}")


if __name__ == "__main__":
    main()
