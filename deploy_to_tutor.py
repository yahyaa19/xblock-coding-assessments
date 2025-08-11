#!/usr/bin/env python3
"""
Deployment Script for Multi-File Coding AI Eval XBlock to Tutor OpenEdX

This script helps deploy the enhanced XBlock to your Tutor OpenEdX instance
following the latest Tutor deployment practices.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

def run_command(command, description="", capture_output=False, shell=False):
    """Run a command with proper error handling."""
    print(f"🔧 {description}")
    print(f"   Command: {command}")
    
    try:
        if shell:
            result = subprocess.run(command, shell=True, capture_output=capture_output, text=True)
        else:
            result = subprocess.run(command.split(), capture_output=capture_output, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ Success!")
            if capture_output and result.stdout:
                return result.stdout.strip()
            return True
        else:
            print(f"   ❌ Failed with exit code {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def check_docker():
    """Check if Docker Desktop is running."""
    print("🐳 Checking Docker Desktop status...")
    
    # Try to get Docker info
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Docker is running!")
            return True
        else:
            print("   ❌ Docker is not running or not accessible")
            return False
    except Exception as e:
        print(f"   ❌ Docker check failed: {e}")
        return False

def start_docker_desktop():
    """Attempt to start Docker Desktop on Windows."""
    print("🚀 Attempting to start Docker Desktop...")
    
    # Try to find and start Docker Desktop
    docker_paths = [
        r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
        r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe"
    ]
    
    for docker_path in docker_paths:
        if os.path.exists(docker_path):
            print(f"   Found Docker Desktop at: {docker_path}")
            try:
                subprocess.Popen([docker_path])
                print("   🔄 Docker Desktop starting... Please wait 30-60 seconds")
                
                # Wait for Docker to start
                for i in range(12):  # Wait up to 60 seconds
                    time.sleep(5)
                    if check_docker():
                        return True
                    print(f"   ⏳ Still waiting... ({(i+1)*5}s)")
                
                print("   ⚠️  Docker Desktop may need more time to start")
                return False
                
            except Exception as e:
                print(f"   ❌ Failed to start Docker Desktop: {e}")
    
    print("   ❌ Docker Desktop not found in standard locations")
    print("   Please start Docker Desktop manually and run this script again")
    return False

def check_tutor_config():
    """Check Tutor configuration."""
    print("📋 Checking Tutor configuration...")
    
    # Check if tutor is configured
    try:
        result = subprocess.run(['tutor', 'config', 'printroot'], capture_output=True, text=True)
        if result.returncode == 0:
            config_root = result.stdout.strip()
            print(f"   ✅ Tutor config root: {config_root}")
            return config_root
        else:
            print("   ❌ Tutor not configured")
            return None
    except Exception as e:
        print(f"   ❌ Tutor config check failed: {e}")
        return None

def install_xblock():
    """Install the XBlock in development mode."""
    print("📦 Installing XBlock in editable mode...")
    
    xblock_dir = Path(__file__).parent
    
    # Change to the XBlock directory
    os.chdir(xblock_dir)
    
    # Install in editable mode
    command = f"{sys.executable} -m pip install -e ."
    return run_command(command, "Installing XBlock package")

def create_tutor_plugin():
    """Create a Tutor plugin for the XBlock."""
    print("🔌 Creating Tutor plugin configuration...")
    
    plugin_content = '''
name: coding_assessments
version: 1.0.0
description: "Multi-File Coding AI Evaluation XBlock with enhanced testing capabilities"

patches:
  common-env-features: |
    CODING_ASSESSMENTS_VERSION: "1.0.0"

  openedx-dockerfile-pre-assets: |
    # Install the coding assessments XBlock
    RUN pip install -e /openedx/xblock-coding-assessments

  openedx-dockerfile-post-python-requirements: |
    # Copy XBlock source code
    COPY --chown=app:app xblock-coding-assessments /openedx/xblock-coding-assessments/

build-image:
  openedx:
    - xblock-coding-assessments

templates:
  openedx-dockerfile: |
    # Additional dependencies for coding assessments
    RUN pip install requests python-json-logger

  k8s-override: |
    # Kubernetes overrides if needed
'''
    
    try:
        # Create plugin directory in Tutor config
        config_root = check_tutor_config()
        if not config_root:
            return False
            
        plugin_dir = Path(config_root) / "plugins"
        plugin_dir.mkdir(exist_ok=True)
        
        plugin_file = plugin_dir / "coding_assessments.yml"
        
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)
        
        print(f"   ✅ Plugin created: {plugin_file}")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create plugin: {e}")
        return False

def enable_tutor_plugin():
    """Enable the Tutor plugin."""
    print("🔌 Enabling Tutor plugin...")
    return run_command("tutor plugins enable coding_assessments", "Enabling plugin")

def build_openedx_image():
    """Build OpenEdX Docker image with the XBlock."""
    print("🏗️  Building OpenEdX image with XBlock...")
    print("   ⚠️  This may take 10-30 minutes depending on your system")
    
    # Use --no-cache to ensure fresh build
    return run_command("tutor images build openedx --no-cache", "Building OpenEdX image")

def start_tutor():
    """Start Tutor OpenEdX in detached mode."""
    print("🚀 Starting Tutor OpenEdX...")
    return run_command("tutor local start -d", "Starting OpenEdX services")

def check_openedx_status():
    """Check if OpenEdX is running properly."""
    print("🔍 Checking OpenEdX status...")
    
    # List running services
    result = run_command("tutor local status", "Checking service status", capture_output=True)
    return result

def create_superuser():
    """Create a superuser for testing (optional)."""
    print("👤 Creating superuser (optional)...")
    print("   You can skip this if you already have admin access")
    
    response = input("   Create superuser? (y/N): ").lower()
    if response == 'y':
        return run_command("tutor local do createuser --staff --superuser admin admin@example.com", 
                          "Creating superuser 'admin'")
    return True

def print_deployment_summary():
    """Print deployment summary and next steps."""
    print("\n" + "="*60)
    print("🎉 DEPLOYMENT SUMMARY")
    print("="*60)
    
    print("\n✅ Your Enhanced Multi-File Coding XBlock should now be deployed!")
    
    print("\n🌐 Access URLs:")
    print("   • LMS (Student View): http://localhost:8000")
    print("   • Studio (Course Creation): http://localhost:8001") 
    print("   • Admin Interface: http://localhost:8000/admin")
    
    print("\n👤 Default Credentials:")
    print("   • Username: admin")
    print("   • Password: Use the password you set during superuser creation")
    
    print("\n📚 Next Steps:")
    print("   1. Open Studio: http://localhost:8001")
    print("   2. Create or edit a course")
    print("   3. Add a new component → Advanced → Multi-File Coding AI Eval")
    print("   4. Configure the XBlock with:")
    print("      - Judge0 API key")
    print("      - Programming language")
    print("      - Test cases")
    print("      - File templates")
    
    print("\n🧪 Testing the Enhanced Features:")
    print("   • Create multi-file projects")
    print("   • Test advanced error handling")
    print("   • Try different comparison types (contains, regex, exact)")
    print("   • Monitor test execution statistics")
    
    print("\n🔧 Troubleshooting:")
    print("   • Check logs: tutor local logs")
    print("   • Restart services: tutor local restart")
    print("   • Check XBlock installation: tutor local run lms pip list | grep coding")

def main():
    """Main deployment function."""
    print("🚀 Multi-File Coding AI Eval XBlock - Tutor Deployment")
    print("=" * 58)
    print("This script will deploy your enhanced XBlock to Tutor OpenEdX")
    print("Make sure you have:")
    print("  • Docker Desktop installed and running")
    print("  • Tutor properly configured")
    print("  • At least 8GB of free disk space")
    print("  • 30-60 minutes for the deployment process")
    
    response = input("\nContinue with deployment? (y/N): ").lower()
    if response != 'y':
        print("Deployment cancelled.")
        return
    
    success_steps = 0
    total_steps = 8
    
    # Step 1: Check Docker
    if not check_docker():
        print("\n🔧 Docker Desktop is not running. Attempting to start...")
        if not start_docker_desktop():
            print("❌ Please start Docker Desktop manually and run this script again.")
            return
    success_steps += 1
    
    # Step 2: Check Tutor config  
    if check_tutor_config():
        success_steps += 1
    else:
        print("❌ Please run 'tutor local quickstart' first to configure Tutor")
        return
    
    # Step 3: Install XBlock
    if install_xblock():
        success_steps += 1
    
    # Step 4: Create Tutor plugin
    if create_tutor_plugin():
        success_steps += 1
    
    # Step 5: Enable plugin
    if enable_tutor_plugin():
        success_steps += 1
    
    # Step 6: Build image (this takes the longest)
    print("\n⚠️  IMPORTANT: The next step will build the Docker image.")
    print("   This process typically takes 15-30 minutes.")
    print("   Please be patient and don't interrupt the process.")
    
    build_response = input("\nProceed with image build? (y/N): ").lower()
    if build_response == 'y':
        if build_openedx_image():
            success_steps += 1
        else:
            print("❌ Image build failed. Check the error messages above.")
            print_deployment_summary()
            return
    else:
        print("⚠️  Skipping image build. You'll need to build manually later.")
    
    # Step 7: Start Tutor
    if start_tutor():
        success_steps += 1
    
    # Step 8: Create superuser (optional)
    if create_superuser():
        success_steps += 1
    
    print(f"\n📋 Deployment completed: {success_steps}/{total_steps} steps successful")
    
    if success_steps >= 6:
        print("✅ Deployment successful!")
        check_openedx_status()
    else:
        print("⚠️  Partial deployment. Some steps may need manual intervention.")
    
    print_deployment_summary()

if __name__ == "__main__":
    main()
