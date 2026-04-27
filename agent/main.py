"""
CodeSage CLI Entry Point

Usage:
    python -m agent.main analyze path/to/file.py
    python -m agent.main scan ./src --output report.md
    python -m agent.main chat
    python -m agent.main score --results results.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def check_env():
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not set. Add it to your .env file.")
        sys.exit(1)


def cmd_analyze(args):
    """Analyze a single file."""
    from agent.core.agent import CodeSageAgent, AgentConfig

    check_env()
    agent = CodeSageAgent(AgentConfig())
    filepath = args.file

    print(f"\n🔍 CodeSage — Analyzing: {filepath}\n{'─' * 50}")
    start = time.time()

    result = agent.run(
        user_message=(
            f"Perform a comprehensive analysis of the file at `{filepath}`. "
            "Identify all technical debt, security vulnerabilities, modernization opportunities, "
            "and anti-patterns. Use your tools to read the file and any related files you discover. "
            "Report every confirmed issue using the report_issue tool before giving your summary."
        ),
        codebase_path=str(Path(filepath).parent),
    )

    elapsed = time.time() - start
    print(result.response)
    print(f"\n{'─' * 50}")
    print(f"⏱  Completed in {elapsed:.1f}s | 🔧 Tools used: {', '.join(result.tools_used)}")
    print(f"📋 Issues registered: {len(result.issues_found)}")

    if args.output:
        Path(args.output).write_text(result.response)
        print(f"💾 Report saved to: {args.output}")


def cmd_scan(args):
    """Scan an entire directory."""
    from agent.core.agent import CodeSageAgent, AgentConfig

    check_env()
    agent = CodeSageAgent(AgentConfig())
    root = args.directory

    print(f"\n🔍 CodeSage — Scanning: {root}\n{'─' * 50}")
    print("🗂  Indexing codebase...")

    start = time.time()
    indexed = agent.memory.index_codebase(root)
    print(f"   Indexed {indexed} files")

    summary = agent.memory.get_summary()
    print(f"   Total lines: {summary['total_lines']:,}")

    result = agent.run(
        user_message=(
            f"I have indexed a codebase at `{root}` with {indexed} files and "
            f"{summary['total_lines']:,} lines of code. "
            "Perform a comprehensive technical debt and security audit. "
            "Use search_pattern to find anti-patterns across all files. "
            "Use get_dependencies to understand the blast radius of critical issues. "
            "Run detect_secrets on configuration and authentication files. "
            "Report every confirmed issue and then provide a prioritized remediation roadmap."
        ),
        codebase_path=root,
    )

    elapsed = time.time() - start
    print(f"\n{result.response}")
    print(f"\n{'─' * 50}")
    print(f"⏱  Completed in {elapsed:.1f}s | Issues: {len(result.issues_found)}")

    if args.output:
        Path(args.output).write_text(result.response)
        print(f"💾 Report saved to: {args.output}")


def cmd_chat(args):
    """Interactive chat mode — ask questions about your codebase."""
    from agent.core.agent import CodeSageAgent, AgentConfig

    check_env()
    agent = CodeSageAgent(AgentConfig())
    codebase = args.codebase

    if codebase:
        print(f"🗂  Indexing {codebase}...")
        count = agent.memory.index_codebase(codebase)
        print(f"   Indexed {count} files.")

    print("\n🧠 CodeSage Chat — Type 'exit' to quit\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input or user_input.lower() in {"exit", "quit"}:
            break

        result = agent.run(user_input, codebase_path=codebase)
        print(f"\nCodeSage: {result.response}\n")


def cmd_score(args):
    """Show scoring methodology and optionally compute a score from a results JSON."""
    from agent.metrics.scorer import PerformanceScorer

    print("\n📊 CodeSage Scoring Methodology\n")
    print("Formula: CWS = (Accuracy × 0.30) + (Depth × 0.25) + (Actionability × 0.20)")
    print("                + (Safety × 0.15) + (Speed × 0.10)")
    print("\nDimension max: 2,000  |  Total max: 10,000")
    print("\nGrade thresholds: S ≥ 9,000 | A ≥ 7,500 | B ≥ 6,000 | C ≥ 4,000 | D < 4,000")

    if args.results:
        data = json.loads(Path(args.results).read_text())
        print(f"\n📈 Loaded results from {args.results}")
        print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(
        prog="codesage",
        description="CodeSage — Legacy Code Modernization Agent",
    )
    sub = parser.add_subparsers(dest="command")

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analyze a single file")
    p_analyze.add_argument("file", help="Path to file to analyze")
    p_analyze.add_argument("--output", "-o", help="Save report to file")
    p_analyze.set_defaults(func=cmd_analyze)

    # scan
    p_scan = sub.add_parser("scan", help="Scan an entire directory")
    p_scan.add_argument("directory", help="Root directory to scan")
    p_scan.add_argument("--output", "-o", help="Save report to file")
    p_scan.set_defaults(func=cmd_scan)

    # chat
    p_chat = sub.add_parser("chat", help="Interactive chat with your codebase")
    p_chat.add_argument("--codebase", "-c", help="Optional: path to index before chatting")
    p_chat.set_defaults(func=cmd_chat)

    # score
    p_score = sub.add_parser("score", help="Show scoring methodology")
    p_score.add_argument("--results", help="Optional: path to JSON results to display")
    p_score.set_defaults(func=cmd_score)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
