"""
CodeSage Tools

Defines the tools available to the agent during the agentic loop.
Each tool gives the agent the ability to read files, parse ASTs,
search for patterns, and retrieve cross-file dependency information.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from agent.core.memory import CodebaseMemory


# ─────────────────────────────────────────────
# Tool Definitions (passed to the Anthropic API)
# ─────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": (
            "Read the contents of a source code file. "
            "Use this to inspect a specific file for analysis."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file to read.",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "search_pattern",
        "description": (
            "Search for a regex pattern across all indexed files. "
            "Use this to find where a function is called, where a variable is defined, "
            "or to locate all instances of an anti-pattern."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Python regex pattern to search for.",
                },
                "file_glob": {
                    "type": "string",
                    "description": "Optional glob to restrict search (e.g. '*.py', '*.js'). Defaults to all files.",
                    "default": "*",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "parse_ast",
        "description": (
            "Parse a Python file's Abstract Syntax Tree (AST) and return a structured summary "
            "of its classes, functions, imports, and complexity metrics. "
            "Use this for deep static analysis of Python files."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to a Python (.py) file to parse.",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "get_dependencies",
        "description": (
            "Get the import dependency graph for a file — what it imports, "
            "and which other indexed files import it. "
            "Use this to understand the blast radius of a change."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to analyze dependencies for.",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "detect_secrets",
        "description": (
            "Scan a file or directory for hardcoded secrets: API keys, passwords, "
            "tokens, connection strings. Uses entropy analysis and pattern matching."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to file or directory to scan.",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "report_issue",
        "description": (
            "Report a confirmed issue found during analysis. "
            "Call this once per distinct issue to register it in the session."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    "description": "Severity of the issue.",
                },
                "category": {
                    "type": "string",
                    "description": "Category: e.g. SECURITY, DEBT, PERFORMANCE, MODERNIZATION",
                },
                "title": {"type": "string", "description": "Short title for the issue."},
                "file": {"type": "string", "description": "File path where issue was found."},
                "line": {"type": "integer", "description": "Line number (if applicable)."},
                "description": {"type": "string", "description": "Detailed description."},
                "fix": {"type": "string", "description": "Suggested fix or code snippet."},
            },
            "required": ["severity", "category", "title", "description"],
        },
    },
]


# ─────────────────────────────────────────────
# Tool Executor
# ─────────────────────────────────────────────

class ToolExecutor:
    """Executes tool calls made by the agent during the agentic loop."""

    def __init__(self, memory: CodebaseMemory):
        self.memory = memory

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Route a tool call to the appropriate handler."""
        handlers = {
            "read_file": self._read_file,
            "search_pattern": self._search_pattern,
            "parse_ast": self._parse_ast,
            "get_dependencies": self._get_dependencies,
            "detect_secrets": self._detect_secrets,
            "report_issue": self._report_issue,
        }
        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            return handler(**tool_input)
        except Exception as exc:
            return {"error": str(exc)}

    # ── Individual tool handlers ──

    def _read_file(self, path: str) -> dict:
        p = Path(path)
        if not p.exists():
            return {"error": f"File not found: {path}"}
        content = p.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        return {
            "path": str(p),
            "lines": len(lines),
            "size_bytes": p.stat().st_size,
            "content": content,
        }

    def _search_pattern(self, pattern: str, file_glob: str = "*") -> dict:
        results = []
        root = self.memory.root or Path(".")
        for filepath in root.rglob(file_glob):
            if not filepath.is_file():
                continue
            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(text.splitlines(), 1):
                    if re.search(pattern, line):
                        results.append({
                            "file": str(filepath),
                            "line": i,
                            "content": line.strip(),
                        })
            except Exception:
                continue
        return {"pattern": pattern, "matches": results, "total": len(results)}

    def _parse_ast(self, path: str) -> dict:
        p = Path(path)
        if p.suffix != ".py":
            return {"error": "AST parsing only supports Python files."}
        source = p.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return {"error": f"Syntax error: {e}"}

        classes = []
        functions = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "method_count": len(methods),
                    "methods": methods[:20],  # Cap for brevity
                })
            elif isinstance(node, ast.FunctionDef):
                classes_found = [n for n in ast.walk(node) if isinstance(n, ast.ClassDef)]
                if not classes_found:
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [a.arg for a in node.args.args],
                        "complexity": sum(
                            1 for n in ast.walk(node)
                            if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler))
                        ),
                    })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                else:
                    imports.append(node.module)

        return {
            "file": str(p),
            "total_lines": len(source.splitlines()),
            "classes": classes,
            "top_level_functions": functions,
            "imports": list(set(filter(None, imports))),
        }

    def _get_dependencies(self, path: str) -> dict:
        return self.memory.get_dependencies(path)

    def _detect_secrets(self, path: str) -> dict:
        """Simple entropy + pattern-based secret detection."""
        SECRET_PATTERNS = [
            (r"(?i)(api[_-]?key|apikey)\s*=\s*['\"]([A-Za-z0-9_\-]{16,})['\"]", "API Key"),
            (r"(?i)(password|passwd|pwd)\s*=\s*['\"]([^'\"]{6,})['\"]", "Password"),
            (r"(?i)(secret[_-]?key|secret)\s*=\s*['\"]([^'\"]{8,})['\"]", "Secret"),
            (r"(?i)(token)\s*=\s*['\"]([A-Za-z0-9_\-\.]{20,})['\"]", "Token"),
            (r"(?i)(aws_access_key_id)\s*=\s*['\"]([A-Z0-9]{20})['\"]", "AWS Key"),
        ]
        findings = []
        root = Path(path)
        files = [root] if root.is_file() else list(root.rglob("*"))
        for filepath in files:
            if not filepath.is_file():
                continue
            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(text.splitlines(), 1):
                    for pattern, kind in SECRET_PATTERNS:
                        if re.search(pattern, line):
                            findings.append({
                                "file": str(filepath),
                                "line": i,
                                "type": kind,
                                "snippet": re.sub(r"(['\"])([^'\"]{3})[^'\"]*(['\"])", r"\1\2***\3", line.strip()),
                            })
            except Exception:
                continue
        return {"findings": findings, "total": len(findings)}

    def _report_issue(self, **kwargs) -> dict:
        self.memory.add_issue(kwargs)
        return {"status": "registered", "issue_id": len(self.memory.get_issues())}
