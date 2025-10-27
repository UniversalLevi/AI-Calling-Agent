/**
 * Database Configuration
 * MongoDB connection and configuration
 */

const mongoose = require('mongoose');

const connectDB = async () => {
  const maxRetries = 5;
  let retries = 0;
  
  while (retries < maxRetries) {
    try {
      const conn = await mongoose.connect(process.env.MONGO_URI || 'mongodb://localhost:27017/sara-dashboard', {
        useNewUrlParser: true,
        useUnifiedTopology: true,
        serverSelectionTimeoutMS: 5000, // Keep trying to send operations for 5 seconds
        socketTimeoutMS: 45000, // Close sockets after 45 seconds of inactivity
      });

      console.log(`✅ MongoDB Connected: ${conn.connection.host}`);
      
      // Initialize default data
      await initializeDefaultData();
      return;
      
    } catch (error) {
      retries++;
      console.error(`❌ MongoDB connection attempt ${retries}/${maxRetries} failed:`, error.message);
      
      if (retries >= maxRetries) {
        console.error('❌ MongoDB connection failed after maximum retries');
        console.error('💡 Make sure MongoDB is running: mongod --dbpath /path/to/data');
        process.exit(1);
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, 2000 * retries));
    }
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
