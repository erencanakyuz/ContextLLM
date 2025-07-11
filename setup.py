#!/usr/bin/env python3
"""
ContextLLM Setup Script
Simple installation for ContextLLM Pro
"""

import sys
import subprocess
import os

def install_requirements():
    """Install requirements from requirements.txt"""
    print("🔧 Installing ContextLLM dependencies...")
    
    # Try user install first (modern Python safe method)
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully (user mode)!")
        return True
    except subprocess.CalledProcessError:
        print("⚠️ User install failed, trying system install...")
        
        # Try system install with --break-system-packages if needed
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ Dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Both installation methods failed!")
            print("🔧 Alternative solutions:")
            print("   1. Create virtual environment: python3 -m venv venv && source venv/bin/activate")
            print("   2. Manual install: pip install --user PyQt6 requests tiktoken")
            print("   3. Use system packages: apt install python3-pyqt6 python3-requests")
            return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def main():
    print("=" * 50)
    print("🚀 ContextLLM Pro Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install requirements
    if not install_requirements():
        return 1
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("   python main.py")
    print("\n💡 For GitHub token (optional):")
    print("   export GITHUB_TOKEN=your_token_here")
    print("\n⭐ If you like this project, please star it on GitHub!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 