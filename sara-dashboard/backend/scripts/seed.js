/**
 * Database Seeder
 * Seeds the database with initial admin user and sample data
 */

const mongoose = require('mongoose');
const bcrypt = require('bcrypt');
require('dotenv').config({ path: '.env.local' });

// Import models
const User = require('../models/User');
const SystemConfig = require('../models/SystemConfig');
const CallLog = require('../models/CallLog');

// Connect to MongoDB
const connectDB = async () => {
  try {
    await mongoose.connect(process.env.MONGO_URI || 'mongodb://localhost:27017/sara-dashboard');
    console.log('✅ Connected to MongoDB');
  } catch (error) {
    console.error('❌ MongoDB connection error:', error.message);
    process.exit(1);
  }
};

// Seed admin user
const seedUsers = async () => {
  try {
    // Check if admin already exists
    const existingAdmin = await User.findOne({ username: 'admin' });
    
    if (existingAdmin) {
      console.log('ℹ️  Admin user already exists');
      return;
    }

    // Create admin user
    const adminUser = new User({
      username: 'admin',
      email: 'admin@sara.ai',
      password: 'admin123', // Will be hashed by pre-save middleware
      role: 'admin',
      firstName: 'Admin',
      lastName: 'User',
      isActive: true,
      permissions: {
        canViewCalls: true,
        canManageCalls: true,
        canViewAnalytics: true,
        canManageUsers: true,
        canManageSystem: true
      }
    });

    await adminUser.save();
    console.log('✅ Admin user created successfully');
    console.log('   Username: admin');
    console.log('   Password: admin123');
    console.log('   Email: admin@sara.ai');
  } catch (error) {
    console.error('❌ Error seeding users:', error.message);
  }
};

// Seed system configuration
const seedSystemConfig = async () => {
  try {
    const existingCount = await SystemConfig.countDocuments();
    
    if (existingCount > 0) {
      console.log(`ℹ️  ${existingCount} system configs already exist`);
      return;
    }

    // Initialize default configurations using the model's static method
    await SystemConfig.initializeDefaults();
  } catch (error) {
    console.error('❌ Error seeding system config:', error.message);
  }
};

// Seed sample call logs
const seedCallLogs = async () => {
  try {
    const existingLogs = await CallLog.countDocuments();
    
    if (existingLogs > 0) {
      console.log(`ℹ️  ${existingLogs} call logs already exist`);
      return;
    }

    const now = new Date();
    const sampleLogs = [
      {
        callId: 'CA' + Math.random().toString(36).substr(2, 32),
        type: 'inbound',
        caller: '+919026505441',
        receiver: '+13502371533',
        status: 'success',
        duration: 125,
        startTime: new Date(now - 3600000),
        endTime: new Date(now - 3475000),
        language: 'mixed',
        transcript: 'User: I want to book a hotel\nBot: Sure! Could you please let me know the location?\nUser: Jaipur\nBot: Great! What is your budget?',
        interruptionCount: 2,
        satisfaction: 'positive',
        metadata: {
          deviceType: 'mobile',
          location: 'India'
        }
      },
      {
        callId: 'CA' + Math.random().toString(36).substr(2, 32),
        type: 'outbound',
        caller: '+13502371533',
        receiver: '+919876543210',
        status: 'success',
        duration: 89,
        startTime: new Date(now - 7200000),
        endTime: new Date(now - 7111000),
        language: 'hi',
        transcript: 'Bot: Namaste! Main Sara hoon.\nUser: Mujhe flight book karni hai',
        interruptionCount: 0,
        satisfaction: 'neutral',
        metadata: {
          deviceType: 'mobile',
          location: 'India'
        }
      },
      {
        callId: 'CA' + Math.random().toString(36).substr(2, 32),
        type: 'inbound',
        caller: '+919123456789',
        receiver: '+13502371533',
        status: 'failed',
        duration: 15,
        startTime: new Date(now - 10800000),
        endTime: new Date(now - 10785000),
        language: 'en',
        transcript: 'Bot: Hi there! I am Sara.\nUser: [No response]',
        interruptionCount: 0,
        satisfaction: 'negative',
        metadata: {
          deviceType: 'mobile',
          location: 'India'
        }
      },
      {
        callId: 'CA' + Math.random().toString(36).substr(2, 32),
        type: 'inbound',
        caller: '+919988776655',
        receiver: '+13502371533',
        status: 'in-progress',
        duration: 0,
        startTime: new Date(now - 300000),
        language: 'mixed',
        transcript: 'Bot: Hi there! I am Sara. How can I help you today?\nUser: I need information about...',
        interruptionCount: 1,
        satisfaction: 'unknown',
        metadata: {
          deviceType: 'mobile',
          location: 'India'
        }
      }
    ];

    await CallLog.insertMany(sampleLogs);
    console.log(`✅ ${sampleLogs.length} sample call logs created successfully`);
  } catch (error) {
    console.error('❌ Error seeding call logs:', error.message);
  }
};

// Main seeder function
const seedDatabase = async () => {
  console.log('\n' + '='.repeat(60));
  console.log('🌱 SARA DASHBOARD - DATABASE SEEDER');
  console.log('='.repeat(60) + '\n');

  await connectDB();

  console.log('📊 Seeding database...\n');

  await seedUsers();
  await seedSystemConfig();
  await seedCallLogs();

  console.log('\n' + '='.repeat(60));
  console.log('✅ DATABASE SEEDING COMPLETED');
  console.log('='.repeat(60));
  console.log('\n🔑 Login Credentials:');
  console.log('   URL: http://localhost:3000');
  console.log('   Username: admin');
  console.log('   Password: admin123');
  console.log('   Email: admin@sara.ai\n');

  process.exit(0);
};

// Run seeder
seedDatabase().catch((error) => {
  console.error('❌ Seeding failed:', error);
  process.exit(1);
});