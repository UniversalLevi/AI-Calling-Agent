"""
Dependency Checker & Auto-Installer
====================================

Checks if all required dependencies are installed and installs missing ones automatically.
Safe to use - won't break existing installations.
"""

import subprocess
import sys
import importlib.util
from typing import List, Tuple, Dict

# Core dependencies required for the bot to function
REQUIRED_PACKAGES = {
    # Core Python packages
    'dotenv': 'python-dotenv==1.0.1',
    'openai': 'openai==1.51.2',
    'flask': 'flask==3.1.3',
    'requests': 'requests==2.32.3',
    'twilio': 'twilio==9.2.3',
    
    # Audio processing
    'numpy': 'numpy==2.1.1',
    'sounddevice': 'sounddevice==0.4.7',
    'soundfile': 'soundfile==0.12.1',
    'pygame': 'pygame==2.5.2',
    'pyaudio': 'pyaudio==0.2.14',
    'wave': 'wave==0.0.2',
    
    # Speech & TTS
    'faster_whisper': 'faster-whisper==1.0.3',
    'gtts': 'gtts==2.5.3',
    'google.generativeai': 'google-generativeai==0.8.3',
    
    # HTTP & networking
    'httpx': 'httpx==0.27.2',
    'httpcore': 'httpcore==1.0.5',
    'psutil': 'psutil==5.9.8',
    
    # Real-time voice processing
    'webrtcvad': 'webrtcvad==2.0.10',
    'librosa': 'librosa==0.10.1',
    'websockets': 'websockets==12.0',
    
    # Text processing
    'indic_transliteration': 'indic-transliteration==2.3.75',
    'regex': 'regex==2025.9.18',
}

# Optional packages (won't fail if missing)
OPTIONAL_PACKAGES = {
    'asyncio_mqtt': 'asyncio-mqtt==0.16.1',
    'pjsua2': 'pjsua2==2.13.1',
    'threading_timer': 'threading-timer==0.1.0',
}


def check_package_installed(package_import_name: str) -> bool:
    """Check if a package is installed and importable."""
    try:
        spec = importlib.util.find_spec(package_import_name)
        return spec is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def install_package(package_spec: str, package_name: str = None) -> bool:
    """
    Install a package using pip.
    
    Args:
        package_spec: Package specification (e.g., 'flask==3.1.3')
        package_name: Display name for the package
        
    Returns:
        True if installation succeeded, False otherwise
    """
    display_name = package_name or package_spec.split('==')[0]
    print(f"   Installing {display_name}...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--quiet', package_spec],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            print(f"   ✅ {display_name} installed successfully")
            return True
        else:
            print(f"   ⚠️  {display_name} installation had warnings")
            # Still return True if package can be imported
            pkg_name = package_spec.split('==')[0].replace('-', '_')
            return check_package_installed(pkg_name)
            
    except subprocess.TimeoutExpired:
        print(f"   ❌ {display_name} installation timed out")
        return False
    except Exception as e:
        print(f"   ❌ {display_name} installation failed: {e}")
        return False


def check_and_install_dependencies(
    verbose: bool = True,
    install_missing: bool = True
) -> Tuple[bool, List[str], List[str]]:
    """
    Check all dependencies and optionally install missing ones.
    
    Args:
        verbose: Print detailed progress
        install_missing: Automatically install missing packages
        
    Returns:
        Tuple of (all_ok, missing_packages, failed_packages)
    """
    if verbose:
        print("\n🔍 Checking dependencies...")
        print("=" * 60)
    
    missing_packages = []
    failed_installs = []
    
    # Check required packages
    for import_name, package_spec in REQUIRED_PACKAGES.items():
        package_name = package_spec.split('==')[0]
        
        if check_package_installed(import_name):
            if verbose:
                print(f"✅ {package_name}")
        else:
            missing_packages.append(package_spec)
            if verbose:
                print(f"❌ {package_name} - MISSING")
    
    # If packages are missing and we should install them
    if missing_packages and install_missing:
        if verbose:
            print(f"\n📦 Installing {len(missing_packages)} missing package(s)...")
            print("=" * 60)
        
        for package_spec in missing_packages:
            package_name = package_spec.split('==')[0]
            success = install_package(package_spec, package_name)
            if not success:
                failed_installs.append(package_name)
    
    # Check optional packages (don't install, just inform)
    if verbose:
        print("\n📋 Optional packages:")
        for import_name, package_spec in OPTIONAL_PACKAGES.items():
            package_name = package_spec.split('==')[0]
            if check_package_installed(import_name):
                print(f"✅ {package_name}")
            else:
                print(f"⚪ {package_name} - Optional (not required)")
    
    # Final status
    all_ok = len(failed_installs) == 0
    
    if verbose:
        print("\n" + "=" * 60)
        if all_ok:
            print("✅ All required dependencies are installed!")
        else:
            print(f"⚠️  {len(failed_installs)} package(s) failed to install:")
            for pkg in failed_installs:
                print(f"   - {pkg}")
            print("\n💡 Try installing manually:")
            print(f"   pip install {' '.join(failed_installs)}")
        print("=" * 60 + "\n")
    
    return all_ok, missing_packages, failed_installs


def verify_critical_imports() -> Tuple[bool, List[str]]:
    """
    Verify that critical modules can actually be imported.
    
    Returns:
        Tuple of (all_ok, failed_imports)
    """
    critical_imports = {
        'Flask app': ('flask', 'Flask'),
        'OpenAI client': ('openai', 'OpenAI'),
        'Twilio client': ('twilio.rest', 'Client'),
        'Faster Whisper': ('faster_whisper', 'WhisperModel'),
        'NumPy': ('numpy', None),
        'Requests': ('requests', None),
    }
    
    failed = []
    
    for name, (module, attr) in critical_imports.items():
        try:
            mod = __import__(module, fromlist=[attr] if attr else [])
            if attr:
                getattr(mod, attr)
        except Exception as e:
            failed.append(f"{name}: {str(e)}")
    
    return len(failed) == 0, failed


def check_environment_file() -> bool:
    """Check if .env file exists."""
    import os
    return os.path.exists('.env')


def run_full_check(auto_install: bool = True, verbose: bool = True) -> bool:
    """
    Run full dependency check with installation.
    
    Args:
        auto_install: Automatically install missing packages
        verbose: Print detailed output
        
    Returns:
        True if all checks passed, False otherwise
    """
    # Check dependencies
    all_ok, missing, failed = check_and_install_dependencies(
        verbose=verbose,
        install_missing=auto_install
    )
    
    if not all_ok:
        return False
    
    # Verify imports work
    if verbose:
        print("🔬 Verifying critical imports...")
    
    imports_ok, failed_imports = verify_critical_imports()
    
    if not imports_ok:
        if verbose:
            print("❌ Some imports failed:")
            for failure in failed_imports:
                print(f"   - {failure}")
        return False
    
    if verbose:
        print("✅ All critical imports verified!\n")
    
    # Check .env file
    if not check_environment_file():
        if verbose:
            print("⚠️  WARNING: .env file not found!")
            print("   Create .env file with your API keys before running the bot.")
            print("   See env.example for reference.\n")
    
    return True


if __name__ == "__main__":
    """Run checks when executed directly."""
    print("\n" + "="*60)
    print("🤖 SARA AI CALLING BOT - Dependency Checker")
    print("="*60)
    
    success = run_full_check(auto_install=True, verbose=True)
    
    if success:
        print("🎉 System is ready to run!")
        print("   Execute: python main.py")
    else:
        print("❌ Some dependencies are missing or failed to install.")
        print("   Please install them manually and try again.")
        sys.exit(1)

