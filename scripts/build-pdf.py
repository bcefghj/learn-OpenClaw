#!/usr/bin/env python3
"""
learn-OpenClaw PDF 生成脚本
将所有 Markdown 课程和面试材料合并为一个 PDF 文件。

依赖安装：
  pip install markdown weasyprint
  # 或者使用 pandoc（推荐）：
  # brew install pandoc          (macOS)
  # sudo apt install pandoc      (Ubuntu)

使用方式：
  python scripts/build-pdf.py              # 使用 pandoc（推荐）
  python scripts/build-pdf.py --engine md  # 使用 markdown+weasyprint
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LESSON_ORDER = [
    "lessons/01-what-is-ai-agent.md",
    "lessons/02-agent-core-concepts.md",
    "lessons/03-what-is-openclaw.md",
    "lessons/04-install-openclaw.md",
    "lessons/05-first-conversation.md",
    "lessons/06-gateway-architecture.md",
    "lessons/07-agent-runner.md",
    "lessons/08-react-loop.md",
    "lessons/09-context-window.md",
    "lessons/10-memory-system.md",
    "lessons/11-skills-system.md",
    "lessons/12-mcp-protocol.md",
    "lessons/13-multi-channel.md",
    "lessons/14-plugin-development.md",
    "lessons/15-automation-workflow.md",
    "lessons/16-security-governance.md",
    "lessons/17-source-code-tour.md",
    "lessons/18-system-design.md",
    "lessons/19-resume-guide.md",
    "lessons/20-mock-interview.md",
]

INTERVIEW_ORDER = [
    "interview/baguweng.md",
    "interview/questions.md",
    "interview/star-interview-scripts.md",
    "interview/resume-template.md",
    "interview/resume-writing-guide.md",
    "interview/project-introduction.md",
    "interview/interviewer-perspective.md",
    "interview/job-market-2026.md",
]

OUTPUT_DIR = PROJECT_ROOT / "docs"


def merge_markdown(files: list[str]) -> str:
    """Merge multiple markdown files into one string with page breaks."""
    parts = []
    for f in files:
        path = PROJECT_ROOT / f
        if path.exists():
            content = path.read_text(encoding="utf-8")
            parts.append(content)
            parts.append("\n\n---\n\n\\newpage\n\n")
        else:
            print(f"  [WARN] File not found: {f}", file=sys.stderr)
    return "\n".join(parts)


def build_with_pandoc(output_path: Path):
    """Use pandoc to convert merged markdown to PDF."""
    all_files = LESSON_ORDER + INTERVIEW_ORDER
    merged = merge_markdown(all_files)

    tmp_file = OUTPUT_DIR / "_merged.md"
    tmp_file.write_text(merged, encoding="utf-8")

    cmd = [
        "pandoc",
        str(tmp_file),
        "-o", str(output_path),
        "--pdf-engine=xelatex",
        "-V", "CJKmainfont=PingFang SC",
        "-V", "geometry:margin=2cm",
        "-V", "fontsize=11pt",
        "--toc",
        "--toc-depth=2",
        "-V", "title=learn-OpenClaw 面试导向完全学习指南",
        "-V", "author=bcefghj",
        "-V", "date=2026",
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    tmp_file.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"pandoc error:\n{result.stderr}", file=sys.stderr)
        print("\nTip: Make sure pandoc and xelatex are installed:")
        print("  brew install pandoc basictex  (macOS)")
        print("  sudo apt install pandoc texlive-xetex  (Ubuntu)")
        return False

    print(f"PDF generated: {output_path}")
    return True


def build_simple_merged(output_path: Path):
    """Fallback: merge all markdown into a single .md file for manual conversion."""
    all_files = LESSON_ORDER + INTERVIEW_ORDER
    merged = merge_markdown(all_files)

    md_output = output_path.with_suffix(".md")
    md_output.write_text(merged, encoding="utf-8")
    print(f"Merged markdown: {md_output}")
    print("Convert to PDF with: pandoc docs/learn-openclaw-merged.md -o docs/learn-openclaw.pdf --pdf-engine=xelatex -V CJKmainfont='PingFang SC'")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build PDF from learn-OpenClaw content")
    parser.add_argument("--engine", choices=["pandoc", "md"], default="pandoc",
                        help="pandoc (recommended) or md (merge only)")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "learn-openclaw.pdf"

    if args.engine == "pandoc":
        if subprocess.run(["which", "pandoc"], capture_output=True).returncode != 0:
            print("pandoc not found, falling back to merge mode")
            build_simple_merged(output_path)
        else:
            build_with_pandoc(output_path)
    else:
        build_simple_merged(output_path)


if __name__ == "__main__":
    main()
