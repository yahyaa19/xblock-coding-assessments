#!/usr/bin/env python3
"""
Simple Deployment Script for Multi-File Coding XBlock

This script provides a step-by-step manual deployment approach.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description=""):
    """Run a command with proper output."""
    print(f"🔧 {description}")
    print(f"   Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success!")
            return True
        else:
            print(f"   ❌ Failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🚀 Simple Multi-File Coding XBlock Deployment")
    print("=" * 50)
    
    # Step 1: Check current directory
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Step 2: Install the XBlock locally (already done)
    print(f"✅ XBlock already installed in development mode")
    
    # Step 3: Build OpenEdX image with custom configuration
    print(f"\n🏗️  Building OpenEdX image...")
    print(f"⚠️  This will take 15-30 minutes. Please be patient.")
    
    response = input("\nProceed with image build? (y/N): ").lower()
    if response != 'y':
        print("Build cancelled. You can run this later with:")
        print("   tutor images build openedx --no-cache")
        return
    
    # Build the image
    if run_command("tutor images build openedx --no-cache", "Building OpenEdX Docker image"):
        print("✅ Image built successfully!")
    else:
        print("❌ Image build failed")
        return
    
    # Step 4: Start Tutor
    print(f"\n🚀 Starting Tutor OpenEdX services...")
    if run_command("tutor local start -d", "Starting OpenEdX"):
        print("✅ OpenEdX started successfully!")
        
        # Wait for services to be ready
        print("⏳ Waiting for services to initialize (30 seconds)...")
        import time
        time.sleep(30)
        
        # Check status
        print("🔍 Checking service status:")
        run_command("tutor local status", "Service status")
        
        print("\n" + "="*50)
        print("🎉 DEPLOYMENT COMPLETED!")
        print("="*50)
        
        print("\n🌐 Your OpenEdX instance is now running at:")
        print("   • LMS: http://localhost:8000")
        print("   • Studio: http://localhost:8001")
        
        print("\n📝 Next Steps:")
        print("   1. Open Studio: http://localhost:8001")
        print("   2. Create or edit a course")
        print("   3. Add 'Advanced' component")
        print("   4. Look for 'Multi-File Coding AI Eval' or similar XBlock")
        
        print("\n🔧 If the XBlock is not visible:")
        print("   1. Check XBlock installation:")
        print("      tutor local run lms pip list | grep xblock-ai-eval")
        print("   2. Check logs:")
        print("      tutor local logs lms")
        print("   3. Restart services:")
        print("      tutor local restart")
        
    else:
        print("❌ Failed to start OpenEdX")

if __name__ == "__main__":
    main()
