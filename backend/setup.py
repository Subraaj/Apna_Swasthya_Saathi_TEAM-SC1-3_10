#!/usr/bin/env python3
"""
Setup script for Apna Swasthya Saathi Backend
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def setup_virtual_environment():
    """Setup virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("📁 Virtual environment already exists")
        return
    
    print("🔄 Creating virtual environment...")
    run_command(f"{sys.executable} -m venv venv", "Virtual environment creation")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    
    # Determine pip command based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_cmd = "venv/bin/pip"
    
    # Upgrade pip first
    run_command(f"{pip_cmd} install --upgrade pip", "Pip upgrade")
    
    # Install requirements
    run_command(f"{pip_cmd} install -r requirements.txt", "Dependencies installation")

def setup_database():
    """Setup database tables"""
    print("🗄️ Setting up database...")
    
    # Create uploads directory
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    print("✅ Uploads directory created")
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    print("✅ Logs directory created")

def create_env_file():
    """Create .env file from example"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("📄 .env file already exists")
        return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ .env file created from example")
        print("⚠️  Please update .env file with your actual configuration values")
    else:
        print("❌ .env.example file not found")

def display_setup_complete():
    """Display setup completion message"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              Setup Complete Successfully! 🎉                 ║
╠══════════════════════════════════════════════════════════════╣
║ Next Steps:                                                  ║
║                                                              ║
║ 1. Update .env file with your configuration:                 ║
║    • Database credentials (Supabase or PostgreSQL)          ║
║    • API keys (Gemini, Hugging Face)                        ║
║    • Email configuration (optional)                         ║
║                                                              ║
║ 2. Activate virtual environment:                             ║
║    • Windows: venv\\Scripts\\activate                         ║
║    • Unix/Linux/macOS: source venv/bin/activate             ║
║                                                              ║
║ 3. Run the application:                                      ║
║    python app.py                                             ║
║                                                              ║
║ 4. Test the API:                                             ║
║    curl http://localhost:5000/health                         ║
║                                                              ║
║ 5. Access API documentation:                                 ║
║    http://localhost:5000/api/v1/info                         ║
╚══════════════════════════════════════════════════════════════╝
    """)

def main():
    """Main setup function"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Apna Swasthya Saathi Backend Setup                 ║
║              AI-Powered Rural Healthcare                     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Setup steps
        check_python_version()
        setup_virtual_environment()
        install_dependencies()
        setup_database()
        create_env_file()
        
        display_setup_complete()
        
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()