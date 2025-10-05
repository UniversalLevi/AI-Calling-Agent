"""
Quick verification script for Sara Dashboard setup
"""

import os
import sys

def check_file(path, description):
    """Check if a file exists"""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def check_directory(path, description):
    """Check if a directory exists"""
    exists = os.path.isdir(path)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def main():
    print("\n" + "="*60)
    print("SARA DASHBOARD - SETUP VERIFICATION")
    print("="*60 + "\n")
    
    all_good = True
    
    # Check main files
    print("📁 Main Files:")
    all_good &= check_file("start_sara.py", "Launcher script")
    all_good &= check_file("main.py", "Calling bot")
    all_good &= check_file(".env", "Environment file")
    print()
    
    # Check dashboard structure
    print("📁 Dashboard Structure:")
    all_good &= check_directory("sara-dashboard", "Dashboard root")
    all_good &= check_file("sara-dashboard/package.json", "Root package.json")
    print()
    
    # Check backend
    print("📁 Backend:")
    all_good &= check_directory("sara-dashboard/backend", "Backend directory")
    all_good &= check_file("sara-dashboard/backend/package.json", "Backend package.json")
    all_good &= check_file("sara-dashboard/backend/server.js", "Server file")
    all_good &= check_directory("sara-dashboard/backend/node_modules", "Backend dependencies")
    print()
    
    # Check frontend
    print("📁 Frontend:")
    all_good &= check_directory("sara-dashboard/frontend", "Frontend directory")
    all_good &= check_file("sara-dashboard/frontend/package.json", "Frontend package.json")
    all_good &= check_file("sara-dashboard/frontend/src/App.js", "App component")
    all_good &= check_file("sara-dashboard/frontend/src/pages/Settings/Settings.js", "Settings page")
    all_good &= check_directory("sara-dashboard/frontend/node_modules", "Frontend dependencies")
    all_good &= check_directory("sara-dashboard/frontend/public", "Public directory")
    all_good &= check_file("sara-dashboard/frontend/public/index.html", "Index HTML")
    print()
    
    # Check critical components
    print("📁 Critical Components:")
    all_good &= check_file("sara-dashboard/frontend/src/components/Layout/Layout.js", "Layout component")
    all_good &= check_file("sara-dashboard/frontend/src/components/Layout/Sidebar.js", "Sidebar component")
    all_good &= check_file("sara-dashboard/frontend/src/components/Layout/Navbar.js", "Navbar component")
    all_good &= check_file("sara-dashboard/frontend/src/contexts/AuthContext.js", "Auth context")
    all_good &= check_file("sara-dashboard/frontend/src/contexts/SocketContext.js", "Socket context")
    print()
    
    # Final result
    print("="*60)
    if all_good:
        print("✅ ALL CHECKS PASSED - SYSTEM READY!")
        print("\nTo start the system:")
        print("  python start_sara.py")
        print("\nThen open: http://localhost:3000")
        print("Login: admin / admin123")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nMissing dependencies? Run:")
        print("  cd sara-dashboard")
        print("  npm install")
        print("  cd backend && npm install")
        print("  cd ../frontend && npm install")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

