"""
Create Initial Dashboard User
==============================

Run this script to create the first admin user for the dashboard.
"""

import sys
import os

# MongoDB connection details
MONGODB_URI = input("Enter MongoDB URI (press Enter for localhost): ").strip() or "mongodb://localhost:27017/sara-dashboard"
ADMIN_EMAIL = input("Enter admin email (press Enter for admin@sara.ai): ").strip() or "admin@sara.ai"
ADMIN_PASSWORD = input("Enter admin password (press Enter for 'admin123'): ").strip() or "admin123"
ADMIN_NAME = input("Enter admin name (press Enter for 'Admin User'): ").strip() or "Admin User"

print("\n📋 Creating user with:")
print(f"   Email: {ADMIN_EMAIL}")
print(f"   Name: {ADMIN_NAME}")
print(f"   MongoDB: {MONGODB_URI}")
print()

# Create Node.js script content
node_script = f'''
const mongoose = require('mongoose');
const bcrypt = require('bcrypt');

// Connect to MongoDB
mongoose.connect('{MONGODB_URI}', {{
    useNewUrlParser: true,
    useUnifiedTopology: true
}}).then(() => {{
    console.log('✅ Connected to MongoDB');
    createUser();
}}).catch(err => {{
    console.error('❌ MongoDB connection error:', err);
    process.exit(1);
}});

// User schema (simplified)
const UserSchema = new mongoose.Schema({{
    name: String,
    email: {{ type: String, unique: true }},
    password: String,
    role: {{ type: String, default: 'admin' }},
    createdAt: {{ type: Date, default: Date.now }}
}});

const User = mongoose.model('User', UserSchema);

async function createUser() {{
    try {{
        // Check if user exists
        const existingUser = await User.findOne({{ email: '{ADMIN_EMAIL}' }});
        if (existingUser) {{
            console.log('⚠️  User already exists:', '{ADMIN_EMAIL}');
            process.exit(0);
        }}
        
        // Hash password
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash('{ADMIN_PASSWORD}', salt);
        
        // Create user
        const user = new User({{
            name: '{ADMIN_NAME}',
            email: '{ADMIN_EMAIL}',
            password: hashedPassword,
            role: 'admin'
        }});
        
        await user.save();
        console.log('✅ Admin user created successfully!');
        console.log('📧 Email:', '{ADMIN_EMAIL}');
        console.log('🔑 Password:', '{ADMIN_PASSWORD}');
        console.log('\\n🎯 You can now login to the dashboard!');
        
        process.exit(0);
    }} catch (error) {{
        console.error('❌ Error creating user:', error);
        process.exit(1);
    }}
}}
'''

# Write Node.js script
script_path = 'create_user_temp.js'
backend_dir = 'sara-dashboard/backend'
os.makedirs(backend_dir, exist_ok=True)

full_script_path = os.path.join(backend_dir, script_path)

with open(full_script_path, 'w', encoding='utf-8') as f:
    f.write(node_script)

print("📝 Script created. Running...")
print()

# Run Node.js script
import subprocess
try:
    result = subprocess.run(
        ['node', script_path],
        cwd=backend_dir,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    # Clean up temp script
    os.remove(full_script_path)
    print("🧹 Cleaned up temporary script")
    
    if result.returncode == 0:
        print()
        print("=" * 60)
        print("✅ DASHBOARD LOGIN CREDENTIALS")
        print("=" * 60)
        print(f"URL: http://localhost:3000")
        print(f"Email: {ADMIN_EMAIL}")
        print(f"Password: {ADMIN_PASSWORD}")
        print("=" * 60)
    
except FileNotFoundError:
    print("❌ Error: Node.js not found. Please install Node.js first.")
    print("   Or run manually:")
    print(f"   cd sara-dashboard/backend")
    print(f"   node {script_path}")
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"   You can run the script manually:")
    print(f"   cd sara-dashboard/backend")
    print(f"   node {script_path}")

