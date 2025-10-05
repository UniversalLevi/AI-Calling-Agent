/**
 * Database Configuration
 * MongoDB connection and configuration
 */

const mongoose = require('mongoose');

const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGO_URI);

    console.log(`✅ MongoDB Connected: ${conn.connection.host}`);
    
    // Initialize default data
    await initializeDefaultData();
    
  } catch (error) {
    console.error('❌ MongoDB connection error:', error);
    process.exit(1);
  }
};

const initializeDefaultData = async () => {
  try {
    // Initialize default admin user
    const User = require('../models/User');
    await User.createDefaultAdmin();
    
    // Initialize default system configurations
    const SystemConfig = require('../models/SystemConfig');
    await SystemConfig.initializeDefaults();
    
    console.log('✅ Default data initialized');
  } catch (error) {
    console.error('❌ Error initializing default data:', error);
  }
};

// Handle connection events
mongoose.connection.on('connected', () => {
  console.log('🔗 Mongoose connected to MongoDB');
});

mongoose.connection.on('error', (err) => {
  console.error('❌ Mongoose connection error:', err);
});

mongoose.connection.on('disconnected', () => {
  console.log('🔌 Mongoose disconnected from MongoDB');
});

// Graceful shutdown
process.on('SIGINT', async () => {
  await mongoose.connection.close();
  console.log('🛑 MongoDB connection closed through app termination');
  process.exit(0);
});

module.exports = connectDB;
