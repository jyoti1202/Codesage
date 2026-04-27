from flask import Flask, render_template, request
import os
import shutil

from agent.core.agent import CodeSageAgent

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".json", ".html", ".css"}


def allowed_file(filename):
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    files = request.files.getlist("files")

    if not files:
        return render_template("index.html", error="Please upload files or folder")

    try:
        project_path = os.path.join(UPLOAD_FOLDER, "project")

        # Remove old project
        if os.path.exists(project_path):
            shutil.rmtree(project_path)

        os.makedirs(project_path, exist_ok=True)

        saved_files = 0

        for file in files:
            if file and allowed_file(file.filename):

                filepath = os.path.join(project_path, file.filename)

                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                saved_files += 1

        if saved_files == 0:
            return render_template("index.html", error="No valid code files found")

        agent = CodeSageAgent()
        result = agent.run(
            user_message="Analyze project",
            codebase_path=project_path
        )

        return render_template("result.html", result=result)

    except Exception as e:
        return render_template("index.html", error=f"Error: {str(e)}")


if __name__ == "__main__":
    app.run(debug=True)