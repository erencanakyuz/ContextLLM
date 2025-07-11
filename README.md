# ContextLLM

Convert large codebases into text format for AI analysis. Process local folders or GitHub repositories completely locally with zero internet sharing.

**Created by:** erencanakyuz

## What It Does

This program converts large codebases into text format completely locally. Select a local folder or GitHub repository, then copy the entire text with one click to web-based LLMs like Google AI Studio (free up to 1M tokens), ChatGPT, or Claude. 

Filter specific files and extensions, then enhance your prompts with 20+ professional templates including anti-hallucination and anti-sycophancy modes that prevent AI from excessive praise.

**Privacy:** All processing occurs locally. No code transmitted to external servers.

## Screenshots

### Main Interface
<div align="center">
  <img width="607" height="575" alt="ContextLLM Main Interface" src="https://github.com/user-attachments/assets/5c2474de-0cd3-43ba-bbad-ac20c974c0db" />
  <p><em>Clean interface for processing local folders and GitHub repositories</em></p>
</div>

### Professional Template Library
<div align="center">
  <img width="1482" height="506" alt="ContextLLM Template System" src="https://github.com/user-attachments/assets/66fec71f-3290-4d3b-a0c6-d0434a40f15c" />
  <p><em>20+ professional prompts for enhanced AI interactions</em></p>
</div>

## Key Features

- **Local Processing:** Complete privacy protection, no external servers
- **GitHub Integration:** Anonymous (60/hour) or authenticated (unlimited) access
- **Smart Filtering:** File type selection, size limits, binary detection
- **Professional Templates:** Anti-hallucination, coding excellence, security audit prompts
- **One-Click Export:** Direct clipboard copy for all major LLMs
- **Token Counting:** Cost estimation for Claude, GPT, Gemini models

## Use Cases

**Security Analysis:** Find vulnerabilities using free AI models
**Bug Detection:** Identify and fix logical errors efficiently  
**Code Quality:** Evaluate structure, patterns, maintainability
**Architecture Review:** Get scalability and improvement recommendations
**Documentation:** Generate API references and technical guides 
 ...

## Quick Start

### Method 1: Automatic Setup (Recommended)

**Windows:**
```cmd
git clone https://github.com/erencanakyuz/ContextLLM
cd ContextLLM
setup.bat
```

**Linux/Mac:**
```bash
git clone https://github.com/erencanakyuz/ContextLLM
cd ContextLLM
chmod +x setup.sh
./setup.sh
```

### Method 2: Manual Setup

```bash
# 1. Clone
git clone https://github.com/erencanakyuz/ContextLLM
cd ContextLLM

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

### Method 3: One-Line Install

**Windows (if py launcher available):**
```cmd
py -m pip install PyQt6 requests tiktoken && py main.py
```

**All platforms:**
```bash
pip install PyQt6 requests tiktoken && python main.py
```

**Requirements:** Python 3.8+

## Troubleshooting

**"python not found" (Windows):** Use `py` instead of `python`

**"externally-managed-environment" (Linux/Mac):** Modern Python protection. Solutions:
```bash
# Option 1: User install (recommended)
pip install --user PyQt6 requests tiktoken

# Option 2: Virtual environment  
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Option 3: System packages (Ubuntu/Debian)
sudo apt install python3-pyqt6 python3-requests
pip install --user tiktoken
```

**Permission errors:** Run setup as administrator (Windows) or use `--user` flag

## Usage

**Local:** Select folder → Choose file types → Process → Copy to AI
**GitHub:** Enter URL → Select branch → Process → Copy to AI


## GitHub Access (Optional)

Set environment variable for unlimited access:
```bash
export GITHUB_TOKEN=your_token_here  # Linux/Mac
set GITHUB_TOKEN=your_token_here     # Windows
```

## License

GPL v3 

---

⭐ **Star this project on GitHub to make me happy!**
