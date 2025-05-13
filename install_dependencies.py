import sys
import subprocess
import os
import platform

def check_python_version():
    """Check if the Python version is compatible."""
    print(f"Python version: {platform.python_version()}")
    major, minor, _ = platform.python_version_tuple()
    
    if int(major) != 3 or int(minor) < 8:
        print("WARNING: This application works best with Python 3.8-3.11")
        input("Press Enter to continue anyway or Ctrl+C to exit...")

def install_package(package_name, version=None):
    """Install a Python package with pip."""
    package_spec = f"{package_name}=={version}" if version else package_name
    print(f"Installing {package_spec}...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_spec])
        return True
    except subprocess.CalledProcessError:
        try:
            # Try without version constraint if specific version fails
            if version:
                print(f"Failed to install {package_spec}, trying without version constraint...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                return True
        except subprocess.CalledProcessError:
            print(f"Failed to install {package_name}")
            return False

def upgrade_pip():
    """Upgrade pip to the latest version."""
    try:
        print("Upgrading pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        return True
    except subprocess.CalledProcessError:
        print("Failed to upgrade pip")
        return False

def main():
    """Main installation function."""
    print("==== Installing dependencies for Robo Trader 2.0 ====")
    
    # Check Python version
    check_python_version()
    
    # Upgrade pip
    upgrade_pip()
    
    # Install required packages with more flexible versioning
    dependencies = [
        ("fastapi", "0.100.0"), 
        ("uvicorn", "0.23.1"),
        ("iqoptionapi", "7.1.1"),
        ("websockets", "11.0.3"),
        ("python-multipart", "0.0.6"),
        ("aiofiles", "23.1.0"),
    ]
    
    # Try to install pandas and numpy with specific versions first
    special_deps = [
        ("numpy", "1.24.4"),
        ("pandas", "2.0.3"),
    ]
    
    for package, version in special_deps:
        success = install_package(package, version)
        if not success:
            # If specific version fails, try without version constraint
            install_package(package)
    
    # Install other dependencies
    for package, version in dependencies:
        install_package(package, version)
    
    print("\n==== Installation Complete ====")
    print("To start the application, run: python app.py")

if __name__ == "__main__":
    main()
