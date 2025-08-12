#!/usr/bin/env python3
"""
Startup script for AI-BlogPlatform
This script checks all dependencies and configurations before starting the Flask app
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set"""
    load_dotenv()
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    optional_vars = ['GEMINI_API_KEY', 'SECRET_KEY']
    
    print("[INFO] Checking environment variables...")
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"[OK] {var} is set")
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            print(f"[OK] {var} is set")
    
    if missing_required:
        print(f"\n[ERROR] Missing required environment variables: {', '.join(missing_required)}")
        print("Please add them to your .env file")
        return False
    
    if missing_optional:
        print(f"\n[WARNING] Missing optional environment variables: {', '.join(missing_optional)}")
        print("Some features may not work without these variables")
    
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    print("\n[INFO] Checking dependencies...")
    
    required_packages = [
        ('flask', 'flask'),
        ('python-dotenv', 'dotenv'),
        ('supabase', 'supabase'),
        ('google-generativeai', 'google.generativeai'),
        ('requests', 'requests'),
        ('werkzeug', 'werkzeug'),
        ('pillow', 'PIL')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"[OK] {package_name} is installed")
        except ImportError:
            missing_packages.append(package_name)
            print(f"[ERROR] {package_name} is missing")
    
    if missing_packages:
        print(f"\n[ERROR] Missing packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n[INFO] Creating directories...")
    
    directories = [
        'static',
        'static/uploads',
        'templates',
        'templates/auth',
        'templates/blog',
        'templates/admin'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"[OK] {directory}/ created/verified")

def main():
    """Main startup function"""
    print("AI-BlogPlatform Startup Check")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        print("\n[ERROR] Dependency check failed. Please install missing packages.")
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("\n[ERROR] Environment check failed. Please configure your .env file.")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("\n[SUCCESS] All checks passed! Starting Flask application...")
    print("[INFO] Application will be available at: http://localhost:5000")
    print("[INFO] Press Ctrl+C to stop the server")
    print("-" * 40)
    
    # Import and run the Flask app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"\n[ERROR] Error starting application: {e}")
        print("\n[HELP] Troubleshooting tips:")
        print("1. Make sure your .env file has correct Supabase credentials")
        print("2. Check if all required tables exist in your Supabase database")
        print("3. Verify your Gemini API key if using AI features")
        sys.exit(1)

if __name__ == "__main__":
    main()
