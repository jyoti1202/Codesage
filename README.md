# 🧠 CodeSage — AI Code Analysis & Modernization Agent  

> An AI-powered agent that helps developers analyze, understand, and improve legacy codebases through automated insights and suggestions.

---

## 🎯 Problem Specialization  

### What Problem Does CodeSage Solve?  

CodeSage focuses on **understanding and improving legacy code**, which is often:

- Hard to read and maintain  
- Poorly documented  
- Built with outdated practices  
- Prone to hidden bugs and security issues  

Developers spend significant time understanding existing code before making changes. CodeSage reduces this effort by providing **clear explanations, issue detection, and improvement suggestions**.

---

### Why This Problem?  

Most AI tools are optimized for writing new code but struggle with:

- Existing messy codebases  
- Multi-file understanding  
- Explaining logic clearly  

CodeSage is designed to help developers **analyze and improve real-world codebases**, not just generate new code.

---

## 🚀 Features  

- 🔍 **Code Analysis** – Understands code structure and logic  
- ⚠️ **Issue Detection** – Identifies bugs and bad practices  
- 🔐 **Security Checks** – Detects common vulnerabilities  
- 💡 **Code Explanation** – Converts code into simple language  
- ⚡ **Optimization Suggestions** – Suggests better coding practices  
- 📁 **Multi-file Support** – Works with multiple uploaded files  

---

## 📁 Project Structure  

```
codesage/
├── app.py / main.py        # Flask application entry point
├── uploads/               # Uploaded files storage
├── templates/             # HTML templates (UI)
│
├── agent/
│   └── core/
│       ├── agent.py       # CodeSageAgent logic
│       ├── tools.py       # Helper functions
│       └── config.py      # Configuration
│
├── requirements.txt
├── .env
├── .env.example
├── .cursorrules
├── .gitignore
└── README.md
```
---

## ⚙️ Technologies Used  

- **Python** → Core language  
- **Flask** → Backend web framework  
- **Custom AI Agent (CodeSageAgent)** → Code analysis engine  
- **HTML, CSS** → Frontend interface  
- **.env (Environment Variables)** → Secure configuration  

---

## 🔄 How It Works  

1. User uploads a code file or project  
2. Flask backend processes and stores the files  
3. The **CodeSageAgent** analyzes the code  
4. The system generates:
   - Code explanations  
   - Issue detection  
   - Optimization suggestions  
5. Results are displayed through a web interface  


---

### ▶️ Run the Project  

```bash
python app.py

## 💻 Languages  

### Built With:
- Python  

### Supported for Analysis:
- Python  
- JavaScript  
- HTML  
- CSS  
- JSON  

---

## 🖥️ Cursor Integration  

CodeSage is configured to work with **Cursor IDE** using `.cursorrules`.

### How to Use:
1. Open the project in Cursor  
2. `.cursorrules` loads automatically  
3. AI suggestions become more focused on code understanding and improvements  

---

## ⚙️ Setup & Installation  

### Prerequisites  

- Python 3.10+  
- pip  

---

### Installation  

```bash
git clone https://github.com/YOUR_USERNAME/codesage.git
cd codesage

python -m venv .venv

# Activate environment
# Windows:
.venv\Scripts\activate

# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt

## 📌 Summary  

CodeSage is a lightweight AI-powered Flask application that helps developers quickly understand, debug, and improve legacy codebases.