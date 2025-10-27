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

// Voice settings specific endpoints (enhanced for humanization)
// Names used: tts_provider, tts_voice_english, tts_voice_hindi, tts_speed, tts_language_preference

// @desc    Get voice settings
// @route   GET /api/system/voice-settings
// @access  Private
module.exports.getVoiceSettings = asyncHandler(async (req, res) => {
  const keys = [
    'tts_provider', 
    'tts_voice_english', 
    'tts_voice_hindi', 
    'tts_speed', 
    'tts_language_preference',
    'humanized_mode',
    'filler_frequency',
    'hindi_bias_threshold'
  ];
  const configs = await SystemConfig.find({ name: { $in: keys }, isActive: true });
  const map = Object.fromEntries(configs.map(c => [c.name, c.value]));
  
  res.json({ 
    success: true, 
    data: {
      tts_provider: map.tts_provider || 'openai',
      tts_voice_english: map.tts_voice_english || 'nova',
      tts_voice_hindi: map.tts_voice_hindi || 'shimmer',
      tts_speed: map.tts_speed || '0.9',
      tts_language_preference: map.tts_language_preference || 'auto',
      humanized_mode: map.humanized_mode || 'true',
      filler_frequency: map.filler_frequency || '0.15',
      hindi_bias_threshold: map.hindi_bias_threshold || '0.8',
      // Available voice options for each provider
      voice_options: {
        openai: {
          english: ['nova', 'shimmer', 'echo', 'fable', 'onyx', 'alloy'],
          hindi: ['shimmer', 'nova', 'alloy'],
          mixed: ['nova', 'shimmer', 'alloy']
        },
        azure: {
          english: ['en-US-AriaNeural', 'en-US-JennyNeural', 'en-US-GuyNeural'],
          hindi: ['hi-IN-SwaraNeural', 'hi-IN-MadhurNeural'],
          mixed: ['en-US-AriaNeural', 'hi-IN-SwaraNeural']
        },
        google: {
          english: ['en-US-Wavenet-A', 'en-US-Wavenet-B', 'en-US-Wavenet-C'],
          hindi: ['hi-IN-Wavenet-A', 'hi-IN-Wavenet-B'],
          mixed: ['en-US-Wavenet-A', 'hi-IN-Wavenet-A']
        }
      }
    }
  });
});

// @desc    Update voice settings
// @route   PUT /api/system/voice-settings
// @access  Private (Admin)
module.exports.updateVoiceSettings = asyncHandler(async (req, res) => {
  const { 
    tts_provider, 
    tts_voice_english, 
    tts_voice_hindi, 
    tts_speed, 
    tts_language_preference,
    humanized_mode,
    filler_frequency,
    hindi_bias_threshold
  } = req.body || {};
  
  const updates = [];
  const userId = req.user?._id;

  const setConfig = async (name, value) => {
    const c = await SystemConfig.updateConfig(name, value, userId);
    updates.push(c);
  };

  // Update all provided settings
  if (tts_provider !== undefined) await setConfig('tts_provider', tts_provider);
  if (tts_voice_english !== undefined) await setConfig('tts_voice_english', tts_voice_english);
  if (tts_voice_hindi !== undefined) await setConfig('tts_voice_hindi', tts_voice_hindi);
  if (tts_speed !== undefined) await setConfig('tts_speed', tts_speed);
  if (tts_language_preference !== undefined) await setConfig('tts_language_preference', tts_language_preference);
  if (humanized_mode !== undefined) await setConfig('humanized_mode', humanized_mode);
  if (filler_frequency !== undefined) await setConfig('filler_frequency', filler_frequency);
  if (hindi_bias_threshold !== undefined) await setConfig('hindi_bias_threshold', hindi_bias_threshold);

  res.json({ success: true, message: 'Voice settings updated', data: updates });
});

// @desc    Test voice settings
// @route   POST /api/system/voice-test
// @access  Private (Admin)
module.exports.testVoiceSettings = asyncHandler(async (req, res) => {
  const { 
    provider, 
    voice, 
    speed, 
    text, 
    language 
  } = req.body;

  if (!provider || !voice || !text) {
    throw new AppError('Provider, voice, and text are required', 400);
  }

  try {
    // This would integrate with your TTS system
    // For now, return a mock response
    const testResult = {
      success: true,
      message: 'Voice test completed',
      data: {
        provider,
        voice,
        speed: speed || '0.9',
        text,
        language: language || 'en',
        audio_url: `/api/system/voice-test-audio/${Date.now()}.mp3`,
        duration: Math.ceil(text.length / 10) // Mock duration
      }
    };

    res.json(testResult);
  } catch (error) {
    throw new AppError(`Voice test failed: ${error.message}`, 500);
  }
});

// @desc    Get humanization settings
// @route   GET /api/system/humanization-settings
// @access  Private
module.exports.getHumanizationSettings = asyncHandler(async (req, res) => {
  const keys = [
    'humanized_mode',
    'filler_frequency',
    'hindi_bias_threshold',
    'tts_speed',
    'emotion_detection_mode',
    'enable_spoken_tone_converter',
    'enable_micro_sentences',
    'enable_semantic_pacing'
  ];
  
  const configs = await SystemConfig.find({ name: { $in: keys }, isActive: true });
  const map = Object.fromEntries(configs.map(c => [c.name, c.value]));
  
  res.json({ 
    success: true, 
    data: {
      humanized_mode: map.humanized_mode === 'true' || map.humanized_mode === undefined,
      filler_frequency: parseFloat(map.filler_frequency) || 0.15,
      hindi_bias_threshold: parseFloat(map.hindi_bias_threshold) || 0.8,
      tts_speed: parseFloat(map.tts_speed) || 0.9,
      emotion_detection_mode: map.emotion_detection_mode || 'hybrid',
      enable_spoken_tone_converter: map.enable_spoken_tone_converter === 'true',
      enable_micro_sentences: map.enable_micro_sentences === 'true',
      enable_semantic_pacing: map.enable_semantic_pacing === 'true'
    }
  });
});

// @desc    Update humanization settings
// @route   PUT /api/system/humanization-settings
// @access  Private (Admin)
module.exports.updateHumanizationSettings = asyncHandler(async (req, res) => {
  const { 
    humanized_mode,
    filler_frequency,
    hindi_bias_threshold,
    tts_speed,
    emotion_detection_mode,
    enable_spoken_tone_converter,
    enable_micro_sentences,
    enable_semantic_pacing
  } = req.body || {};
  
  const updates = [];
  const userId = req.user?._id;

  const setConfig = async (name, value) => {
    const c = await SystemConfig.updateConfig(name, value, userId);
    updates.push(c);
  };

  // Update all provided settings
  if (humanized_mode !== undefined) await setConfig('humanized_mode', humanized_mode.toString());
  if (filler_frequency !== undefined) await setConfig('filler_frequency', filler_frequency.toString());
  if (hindi_bias_threshold !== undefined) await setConfig('hindi_bias_threshold', hindi_bias_threshold.toString());
  if (tts_speed !== undefined) await setConfig('tts_speed', tts_speed.toString());
  if (emotion_detection_mode !== undefined) await setConfig('emotion_detection_mode', emotion_detection_mode);
  if (enable_spoken_tone_converter !== undefined) await setConfig('enable_spoken_tone_converter', enable_spoken_tone_converter.toString());
  if (enable_micro_sentences !== undefined) await setConfig('enable_micro_sentences', enable_micro_sentences.toString());
  if (enable_semantic_pacing !== undefined) await setConfig('enable_semantic_pacing', enable_semantic_pacing.toString());

  res.json({ success: true, message: 'Humanization settings updated', data: updates });
});