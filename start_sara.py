"""
Sara Calling Bot with Dashboard Launcher
Starts both the calling bot and the dashboard with a single command
"""

import os
import sys
import subprocess
import time
from datetime import datetime
import signal
import atexit
import threading

# Process list to track for cleanup
processes = []

def log_to_file(message, log_file="dashboard.log"):
    """Log message to file with timestamp - text only"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(log_file, 'a', encoding='utf-8', errors='replace') as f:
            # Ensure message is string and filter out non-printable characters
            clean_message = ''.join(char for char in str(message) if char.isprintable() or char in '\n\r\t')
            f.write(f"[{timestamp}] {clean_message}\n")
    except Exception as e:
        print(f"Error writing to log: {e}")

def cleanup():
    """Clean up all processes on exit"""
    print("\n🔄 Shutting down all services...")
    log_to_file("Shutting down all services")
    
    for process in processes:
        try:
            if process.poll() is None:  # Process is still running
                process.terminate()
                process.wait(timeout=5)
        except Exception as e:
            log_to_file(f"Error terminating process: {e}")
            
    print("✅ All services stopped")
    log_to_file("All services stopped")

# Register cleanup function
atexit.register(cleanup)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n⚠️ Received interrupt signal")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def check_node_installed():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            log_to_file(f"Node.js is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    log_to_file("Node.js is not installed")
    return False

def stream_output(pipe, log_file):
    """Stream process output to log file (text only)"""
    try:
        with open(log_file, 'a', encoding='utf-8', errors='replace') as f:
            for line in iter(pipe.readline, ''):
                if line:
                    # Filter out non-printable characters except newlines
                    clean_line = ''.join(char for char in line if char.isprintable() or char in '\n\r\t')
                    if clean_line.strip():  # Only write non-empty lines
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        f.write(f"[{timestamp}] {clean_line}")
                        f.flush()
    except Exception as e:
        log_to_file(f"Error streaming output: {e}")

def start_dashboard():
    """Start the Sara Dashboard"""
    dashboard_path = os.path.join(os.getcwd(), 'sara-dashboard')
    
    if not os.path.exists(dashboard_path):
        log_to_file("Dashboard directory not found")
        print("❌ Dashboard directory not found!")
        return None
    
    log_to_file("Starting Sara Dashboard...")
    print("🚀 Starting Sara Dashboard...")
    
    # Start dashboard with npm run dev
    process = subprocess.Popen(
        ['npm', 'run', 'dev'],
        cwd=dashboard_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1,
        universal_newlines=True
    )
    
    # Start thread to stream output
    output_thread = threading.Thread(
        target=stream_output, 
        args=(process.stdout, 'dashboard.log'),
        daemon=True
    )
    output_thread.start()
    
    processes.append(process)
    log_to_file(f"Dashboard started (PID: {process.pid})")
    print(f"✅ Dashboard started (PID: {process.pid})")
    
    return process

def start_calling_bot():
    """Start the Sara Calling Bot"""
    log_to_file("Sara Calling Bot is available via main.py")
    print("📞 Sara Calling Bot is available via main.py")
    print("   Note: Run 'python main.py' separately to start the calling bot")
    
    # Don't automatically start the calling bot as it requires user interaction
    # Users should run it separately when needed
    return None

def main():
    """Main launcher function"""
    print("\n" + "="*60)
    print("🤖 SARA AI CALLING BOT WITH DASHBOARD")
    print("="*60 + "\n")
    
    # Clear old logs
    for log_file in ['dashboard.log', 'calling_bot.log']:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Log started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
    
    log_to_file("="*60)
    log_to_file("SARA AI CALLING BOT WITH DASHBOARD")
    log_to_file("="*60)
    
    # Check Node.js
    if not check_node_installed():
        print("❌ Node.js is not installed. Please install Node.js first.")
        print("🔗 Download from: https://nodejs.org/")
        return
    
    # Start Dashboard
    dashboard_process = start_dashboard()
    if not dashboard_process:
        return
    
    # Wait a bit for dashboard to initialize
    print("⏳ Waiting for dashboard to initialize...")
    time.sleep(3)
    
    # Start Calling Bot
    bot_process = start_calling_bot()
    
    print("\n" + "="*60)
    print("✅ DASHBOARD STARTED")
    print("="*60)
    print("\n🌐 DASHBOARD:")
    print("   Frontend: http://localhost:3000")
    print("   Backend:  http://localhost:5000")
    print("   Credentials: admin / admin123")
    print("\n📞 CALLING BOT:")
    print("   To start the calling bot, run in a separate terminal:")
    print("   python main.py")
    print("\n📋 LOGS:")
    print("   Dashboard: dashboard.log (text only)")
    print("\n⚠️ Press Ctrl+C to stop the dashboard")
    print("="*60 + "\n")
    
    log_to_file("All services started successfully")
    log_to_file(f"Dashboard Frontend: http://localhost:3000")
    log_to_file(f"Dashboard Backend: http://localhost:5000")
    
    try:
        # Keep the script running and monitor processes
        while True:
            # Check if dashboard process is still running
            if dashboard_process and dashboard_process.poll() is not None:
                log_to_file("Dashboard process stopped unexpectedly")
                print("⚠️ Dashboard process stopped unexpectedly")
                break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
