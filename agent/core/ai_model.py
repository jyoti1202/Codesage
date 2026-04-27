# agent/core/ai_model.py

from transformers import pipeline

# ✅ Load model globally (VERY IMPORTANT)
classifier = pipeline("text-classification", model="microsoft/codebert-base")


def analyze_with_ai(code):
    try:
        if not code.strip():
            return "No code provided"

        result = classifier(code[:512])

        label = result[0]["label"]
        score = result[0]["score"]

        # Make it human readable
        if score > 0.8:
            return f"High confidence pattern detected: {label}"
        else:
            return f"Low confidence pattern: {label}"

    except Exception as e:
        return f"AI Error: {str(e)}"