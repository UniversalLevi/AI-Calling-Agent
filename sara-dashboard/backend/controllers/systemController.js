/**
 * System Controller
 * Handles all system configuration and management endpoints
 */

const SystemConfig = require('../models/SystemConfig');
const { asyncHandler, AppError } = require('../middleware/errorHandler');

// @desc    Get all system configurations
// @route   GET /api/system/config
// @access  Private
const getSystemConfigs = asyncHandler(async (req, res) => {
  const { category } = req.query;

  let configs;
  if (category) {
    configs = await SystemConfig.getByCategory(category);
  } else {
    configs = await SystemConfig.getAllActive();
  }

  res.json({
    success: true,
    data: configs
  });
});

// @desc    Get system configuration by name
// @route   GET /api/system/config/:name
// @access  Private
const getSystemConfig = asyncHandler(async (req, res) => {
  const config = await SystemConfig.findOne({ 
    name: req.params.name, 
    isActive: true 
  });

  if (!config) {
    throw new AppError('Configuration not found', 404);
  }

  res.json({
    success: true,
    data: config
  });
});

// @desc    Update system configuration
// @route   PUT /api/system/config/:name
// @access  Private (Admin only)
const updateSystemConfig = asyncHandler(async (req, res) => {
  const { value } = req.body;

  if (value === undefined) {
    throw new AppError('Value is required', 400);
  }

  const config = await SystemConfig.updateConfig(
    req.params.name,
    value,
    req.user._id
  );

  res.json({
    success: true,
    message: 'Configuration updated successfully',
    data: config
  });
});

// @desc    Bulk update system configurations
// @route   PUT /api/system/config
// @access  Private (Admin only)
const bulkUpdateSystemConfigs = asyncHandler(async (req, res) => {
  const { configs } = req.body;

  if (!Array.isArray(configs)) {
    throw new AppError('Configs must be an array', 400);
  }

  const updatedConfigs = [];

  for (const config of configs) {
    const { name, value } = config;
    
    if (!name || value === undefined) {
      throw new AppError('Name and value are required for each config', 400);
    }

    const updatedConfig = await SystemConfig.updateConfig(
      name,
      value,
      req.user._id
    );
    
    updatedConfigs.push(updatedConfig);
  }

  res.json({
    success: true,
    message: 'Configurations updated successfully',
    data: updatedConfigs
  });
});

// @desc    Get system analytics
// @route   GET /api/system/analytics
// @access  Private
const getSystemAnalytics = asyncHandler(async (req, res) => {
  const { period = '7d' } = req.query;
  
  let days;
  switch (period) {
    case '1d': days = 1; break;
    case '7d': days = 7; break;
    case '30d': days = 30; break;
    case '90d': days = 90; break;
    default: days = 7;
  }

  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  // Get various system metrics
  const [
    callStats,
    userStats,
    systemHealth,
    performanceMetrics
  ] = await Promise.all([
    getCallAnalytics(startDate),
    getUserAnalytics(),
    getSystemHealth(),
    getPerformanceMetrics(startDate)
  ]);

  res.json({
    success: true,
    data: {
      period,
      callStats,
      userStats,
      systemHealth,
      performanceMetrics
    }
  });
});

// @desc    Get system health status
// @route   GET /api/system/health
// @access  Private
const getSystemHealth = asyncHandler(async (req, res) => {
  const health = await getSystemHealthStatus();

  res.json({
    success: true,
    data: health
  });
});

// @desc    Initialize default configurations
// @route   POST /api/system/init-defaults
// @access  Private (Admin only)
const initializeDefaults = asyncHandler(async (req, res) => {
  await SystemConfig.initializeDefaults();

  res.json({
    success: true,
    message: 'Default configurations initialized successfully'
  });
});

// @desc    Export system configurations
// @route   GET /api/system/export
// @access  Private (Admin only)
const exportConfigs = asyncHandler(async (req, res) => {
  const configs = await SystemConfig.find({ isActive: true })
    .select('-__v -createdAt -updatedAt');

  res.json({
    success: true,
    data: configs
  });
});

// @desc    Import system configurations
// @route   POST /api/system/import
// @access  Private (Admin only)
const importConfigs = asyncHandler(async (req, res) => {
  const { configs } = req.body;

  if (!Array.isArray(configs)) {
    throw new AppError('Configs must be an array', 400);
  }

  const importedConfigs = [];

  for (const configData of configs) {
    const existingConfig = await SystemConfig.findOne({ name: configData.name });
    
    if (existingConfig) {
      // Update existing config
      existingConfig.value = configData.value;
      existingConfig.description = configData.description;
      existingConfig.lastModifiedBy = req.user._id;
      await existingConfig.save();
      importedConfigs.push(existingConfig);
    } else {
      // Create new config
      const newConfig = await SystemConfig.create({
        ...configData,
        lastModifiedBy: req.user._id
      });
      importedConfigs.push(newConfig);
    }
  }

  res.json({
    success: true,
    message: 'Configurations imported successfully',
    data: importedConfigs
  });
});

// Helper function to get call analytics
const getCallAnalytics = async (startDate) => {
  const CallLog = require('../models/CallLog');
  
  const stats = await CallLog.getCallStats(startDate, new Date());
  const dailyTrends = await CallLog.getDailyTrends(7);
  
  return {
    totalCalls: stats.totalCalls,
    successfulCalls: stats.successfulCalls,
    failedCalls: stats.failedCalls,
    successRate: stats.totalCalls > 0 
      ? ((stats.successfulCalls / stats.totalCalls) * 100).toFixed(2)
      : 0,
    averageDuration: stats.averageDuration,
    dailyTrends
  };
};

// Helper function to get user analytics
const getUserAnalytics = async () => {
  const User = require('../models/User');
  
  const stats = await User.getUserStats();
  const totalUsers = await User.countDocuments();
  const activeUsers = await User.countDocuments({ isActive: true });
  
  return {
    totalUsers,
    activeUsers,
    inactiveUsers: totalUsers - activeUsers,
    roleDistribution: stats
  };
};

// Helper function to get system health status
const getSystemHealthStatus = async () => {
  const CallLog = require('../models/CallLog');
  const User = require('../models/User');
  
  try {
    // Check database connectivity
    await CallLog.findOne().limit(1);
    await User.findOne().limit(1);
    
    // Get recent call success rate
    const recentDate = new Date();
    recentDate.setHours(recentDate.getHours() - 24);
    
    const recentStats = await CallLog.getCallStats(recentDate, new Date());
    const successRate = recentStats.totalCalls > 0 
      ? (recentStats.successfulCalls / recentStats.totalCalls) * 100
      : 100;
    
    // Determine health status
    let status = 'healthy';
    if (successRate < 80) status = 'warning';
    if (successRate < 60) status = 'critical';
    
    return {
      status,
      database: 'connected',
      successRate: successRate.toFixed(2),
      uptime: process.uptime(),
      memoryUsage: process.memoryUsage(),
      timestamp: new Date()
    };
  } catch (error) {
    return {
      status: 'critical',
      database: 'disconnected',
      error: error.message,
      timestamp: new Date()
    };
  }
};

// Helper function to get performance metrics
const getPerformanceMetrics = async (startDate) => {
  const CallLog = require('../models/CallLog');
  
  const metrics = await CallLog.aggregate([
    {
      $match: {
        createdAt: { $gte: startDate }
      }
    },
    {
      $group: {
        _id: null,
        avgDuration: { $avg: '$duration' },
        maxDuration: { $max: '$duration' },
        minDuration: { $min: '$duration' },
        totalDuration: { $sum: '$duration' },
        avgInterruptions: { $avg: '$interruptionCount' }
      }
    }
  ]);
  
  return metrics[0] || {
    avgDuration: 0,
    maxDuration: 0,
    minDuration: 0,
    totalDuration: 0,
    avgInterruptions: 0
  };
};

module.exports = {
  getSystemConfigs,
  getSystemConfig,
  updateSystemConfig,
  bulkUpdateSystemConfigs,
  getSystemAnalytics,
  getSystemHealth,
  initializeDefaults,
  exportConfigs,
  importConfigs
};
