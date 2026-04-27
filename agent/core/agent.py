# agent/core/agent.py

import os
from .ai_model import analyze_with_ai


class CodeSageAgent:

    def __init__(self):
        # Supported code file types
        self.supported_extensions = (".py", ".js", ".ts", ".json", ".html", ".css")

    def is_valid_file(self, filename):
        return filename.lower().endswith(self.supported_extensions)

    def read_files(self, path):
        """
        Read all supported files safely (handles encoding issues)
        """
        code_data = []

        # Case 1: Single file
        if os.path.isfile(path):
            if self.is_valid_file(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        code_data.append((path, content))
                except Exception:
                    pass

        # Case 2: Folder
        else:
            for root, _, files in os.walk(path):
                for file in files:
                    if self.is_valid_file(file):
                        full_path = os.path.join(root, file)
                        try:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                                code_data.append((full_path, content))
                        except Exception:
                            # Skip unreadable/binary files
                            continue

        return code_data

    def rule_based_analysis(self, content):
        """
        Rule-based checks
        """
        issues = []

        if "eval(" in content:
            issues.append({"issue": "Unsafe eval usage", "severity": "High"})

        if "==" in content:
            issues.append({"issue": "Use of == instead of ===", "severity": "Medium"})

        if "console.log" in content:
            issues.append({"issue": "Debug statement found", "severity": "Low"})

        if "TODO" in content or "FIXME" in content:
            issues.append({"issue": "Pending TODO/FIXME", "severity": "Low"})

        if len(content.splitlines()) > 200:
            issues.append({"issue": "Large file (>200 lines)", "severity": "Medium"})

        return issues

    def run(self, user_message, codebase_path):
        """
        Main execution function
        """
        files_data = self.read_files(codebase_path)

        final_output = []

        for file_path, content in files_data:
            file_result = {
                "file": file_path,
                "rule_issues": self.rule_based_analysis(content),
                "ai_analysis": analyze_with_ai(content)
            }

            final_output.append(file_result)

        return {
            "total_files": len(final_output),
            "results": final_output
        }