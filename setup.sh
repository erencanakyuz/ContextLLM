#!/bin/bash

echo "=========================================="
echo " ContextLLM Pro - Linux/Mac Setup"
echo "=========================================="
echo

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3.8+ using your package manager"
    exit 1
fi

echo "✅ Python 3 detected: $(python3 --version)"
echo

# Install requirements
echo "🔧 Installing dependencies..."

# Try user install first (modern Python safe method)
if python3 -m pip install --user -r requirements.txt; then
    echo "✅ Dependencies installed successfully (user mode)!"
else
    echo "⚠️ User install failed, trying alternatives..."
    echo
    echo "🔧 Alternative solutions:"
    echo "   1. Virtual environment:"
    echo "      python3 -m venv venv"
    echo "      source venv/bin/activate"
    echo "      pip install -r requirements.txt"
    echo
    echo "   2. Manual install:"
    echo "      pip install --user PyQt6 requests tiktoken"
    echo
    echo "   3. System packages (Ubuntu/Debian):"
    echo "      sudo apt install python3-pyqt6 python3-requests python3-pip"
    echo "      pip install --user tiktoken"
    echo
    exit 1
fi

echo
echo "🎉 Setup completed successfully!"
echo
echo "📋 Next steps:"
echo "   python3 main.py"
echo
echo "💡 For GitHub token (optional):"
echo "   export GITHUB_TOKEN=your_token_here"
echo
echo "⭐ If you like this project, please star it on GitHub!"
echo 