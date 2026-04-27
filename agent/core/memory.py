class CodebaseMemory:
    def __init__(self):
        self.files = {}
        self.total_lines = 0

    def index_codebase(self, root_path):
        import os

        count = 0

        for root, _, files in os.walk(root_path):
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".json")):
                    path = os.path.join(root, file)

                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        self.files[path] = content
                        self.total_lines += len(content.splitlines())
                        count += 1
                    except:
                        pass

        return count

    def get_summary(self):
        return {
            "total_lines": self.total_lines
        }

    def get_issues(self):
        return []