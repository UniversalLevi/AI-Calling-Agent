/**
 * SystemConfig Model
 * Database schema for system configuration and settings
 */

const mongoose = require('mongoose');

const systemConfigSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true
  },
  category: {
    type: String,
    enum: ['voice', 'language', 'call', 'security', 'notification', 'integration'],
    required: true
  },
  value: {
    type: mongoose.Schema.Types.Mixed,
    required: true
  },
  dataType: {
    type: String,
    enum: ['string', 'number', 'boolean', 'array', 'object'],
    required: true
  },
  description: {
    type: String,
    trim: true
  },
  isActive: {
    type: Boolean,
    default: true
  },
  isEditable: {
    type: Boolean,
    default: true
  },
  validation: {
    min: Number,
    max: Number,
    pattern: String,
    options: [String] // For dropdown/select options
  },
  lastModifiedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Indexes
systemConfigSchema.index({ name: 1 }, { unique: true });
systemConfigSchema.index({ category: 1 });
systemConfigSchema.index({ isActive: 1 });

// Pre-save middleware to update timestamp
systemConfigSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

// Static method to get configuration by category
systemConfigSchema.statics.getByCategory = async function(category) {
  return await this.find({ category, isActive: true }).sort({ name: 1 });
};

// Static method to get all active configurations
systemConfigSchema.statics.getAllActive = async function() {
  return await this.find({ isActive: true }).sort({ category: 1, name: 1 });
};

// Static method to update configuration
systemConfigSchema.statics.updateConfig = async function(name, value, userId) {
  let config = await this.findOne({ name, isActive: true });
  
  if (!config) {
    // Create new configuration if it doesn't exist
    console.log(`Creating new configuration: ${name}`);
    config = await this.create({
      name: name,
      category: this._getCategoryFromName(name),
      value: value,
      dataType: this._getDataTypeFromValue(value),
      description: `Auto-generated configuration for ${name}`,
      isActive: true,
      isEditable: true,
      lastModifiedBy: userId
    });
    return config;
  }
  
  if (!config.isEditable) {
    throw new Error(`Configuration '${name}' is not editable`);
  }
  
  // Validate value based on data type
  const validatedValue = this.validateValue(value, config.dataType, config.validation);
  
  config.value = validatedValue;
  config.lastModifiedBy = userId;
  config.updatedAt = new Date();
  
  return await config.save();
};

// Static method to validate configuration value
systemConfigSchema.statics.validateValue = function(value, dataType, validation) {
  let validatedValue;
  
  switch (dataType) {
    case 'string':
      validatedValue = String(value);
      if (validation?.pattern && !new RegExp(validation.pattern).test(validatedValue)) {
        throw new Error(`Value does not match required pattern`);
      }
      break;
      
    case 'number':
      validatedValue = Number(value);
      if (isNaN(validatedValue)) {
        throw new Error('Value must be a valid number');
      }
      if (validation?.min !== undefined && validatedValue < validation.min) {
        throw new Error(`Value must be at least ${validation.min}`);
      }
      if (validation?.max !== undefined && validatedValue > validation.max) {
        throw new Error(`Value must be at most ${validation.max}`);
      }
      break;
      
    case 'boolean':
      validatedValue = Boolean(value);
      break;
      
    case 'array':
      if (!Array.isArray(value)) {
        throw new Error('Value must be an array');
      }
      validatedValue = value;
      break;
      
    case 'object':
      if (typeof value !== 'object' || Array.isArray(value)) {
        throw new Error('Value must be an object');
      }
      validatedValue = value;
      break;
      
    default:
      validatedValue = value;
  }
  
  return validatedValue;
};

// Helper method to determine category from configuration name
systemConfigSchema.statics._getCategoryFromName = function(name) {
  if (name.startsWith('tts_') || name.includes('voice')) return 'voice';
  if (name.includes('language') || name.includes('hindi') || name.includes('english')) return 'language';
  if (name.includes('call') || name.includes('timeout') || name.includes('retry')) return 'call';
  if (name.includes('security') || name.includes('session') || name.includes('login')) return 'security';
  if (name.includes('notification') || name.includes('email') || name.includes('dashboard')) return 'notification';
  if (name.includes('integration') || name.includes('webhook') || name.includes('api')) return 'integration';
  return 'voice'; // Default to voice for TTS-related settings
};

// Helper method to determine data type from value
systemConfigSchema.statics._getDataTypeFromValue = function(value) {
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return 'number';
  if (Array.isArray(value)) return 'array';
  if (typeof value === 'object' && value !== null) return 'object';
  return 'string'; // Default to string
};

// Static method to initialize default configurations
systemConfigSchema.statics.initializeDefaults = async function() {
  const defaultConfigs = [
    // Voice configurations
    {
      name: 'tts_provider',
      category: 'voice',
      value: 'openai',
      dataType: 'string',
      description: 'TTS voice provider (openai, azure, google)',
      validation: {
        options: ['openai', 'azure', 'google']
      }
    },
    {
      name: 'tts_voice_english',
      category: 'voice',
      value: 'nova',
      dataType: 'string',
      description: 'English TTS voice',
      validation: {
        options: ['nova', 'shimmer', 'echo', 'fable', 'onyx', 'alloy']
      }
    },
    {
      name: 'tts_voice_hindi',
      category: 'voice',
      value: 'shimmer',
      dataType: 'string',
      description: 'Hindi TTS voice',
      validation: {
        options: ['shimmer', 'nova', 'alloy']
      }
    },
    {
      name: 'tts_speed',
      category: 'voice',
      value: 1.0,
      dataType: 'number',
      description: 'Speech speed multiplier',
      validation: {
        min: 0.5,
        max: 2.0
      }
    },
    {
      name: 'tts_language_preference',
      category: 'voice',
      value: 'auto',
      dataType: 'string',
      description: 'Language preference for TTS',
      validation: {
        options: ['auto', 'english', 'hindi', 'mixed']
      }
    },
    {
      name: 'humanized_mode',
      category: 'voice',
      value: false,
      dataType: 'boolean',
      description: 'Enable humanized speech mode'
    },
    {
      name: 'filler_frequency',
      category: 'voice',
      value: 0.15,
      dataType: 'number',
      description: 'Frequency of filler words',
      validation: {
        min: 0.0,
        max: 1.0
      }
    },
    {
      name: 'hindi_bias_threshold',
      category: 'voice',
      value: 0.8,
      dataType: 'number',
      description: 'Threshold for Hindi language bias',
      validation: {
        min: 0.0,
        max: 1.0
      }
    },
    {
      name: 'emotion_detection_mode',
      category: 'voice',
      value: 'hybrid',
      dataType: 'string',
      description: 'Emotion detection mode',
      validation: {
        options: ['hybrid', 'keyword', 'gpt']
      }
    },
    {
      name: 'enable_spoken_tone_converter',
      category: 'voice',
      value: true,
      dataType: 'boolean',
      description: 'Enable spoken tone converter'
    },
    {
      name: 'enable_micro_sentences',
      category: 'voice',
      value: true,
      dataType: 'boolean',
      description: 'Enable micro sentences'
    },
    {
      name: 'enable_semantic_pacing',
      category: 'voice',
      value: true,
      dataType: 'boolean',
      description: 'Enable semantic pacing'
    },
    
    // Language configurations
    {
      name: 'default_language',
      category: 'language',
      value: 'mixed',
      dataType: 'string',
      description: 'Default language for conversations',
      validation: {
        options: ['en', 'hi', 'mixed']
      }
    },
    {
      name: 'language_detection',
      category: 'language',
      value: true,
      dataType: 'boolean',
      description: 'Enable automatic language detection'
    },
    
    // Call configurations
    {
      name: 'max_concurrent_calls',
      category: 'call',
      value: 10,
      dataType: 'number',
      description: 'Maximum number of concurrent calls',
      validation: {
        min: 1,
        max: 100
      }
    },
    {
      name: 'call_timeout',
      category: 'call',
      value: 300,
      dataType: 'number',
      description: 'Call timeout in seconds',
      validation: {
        min: 60,
        max: 1800
      }
    },
    {
      name: 'retry_limit',
      category: 'call',
      value: 3,
      dataType: 'number',
      description: 'Maximum retry attempts for failed calls',
      validation: {
        min: 0,
        max: 10
      }
    },
    {
      name: 'interruption_enabled',
      category: 'call',
      value: true,
      dataType: 'boolean',
      description: 'Enable call interruption feature'
    },
    
    // Security configurations
    {
      name: 'session_timeout',
      category: 'security',
      value: 3600,
      dataType: 'number',
      description: 'Session timeout in seconds',
      validation: {
        min: 300,
        max: 86400
      }
    },
    {
      name: 'max_login_attempts',
      category: 'security',
      value: 5,
      dataType: 'number',
      description: 'Maximum login attempts before lockout',
      validation: {
        min: 3,
        max: 10
      }
    },
    
    // Notification configurations
    {
      name: 'email_notifications',
      category: 'notification',
      value: true,
      dataType: 'boolean',
      description: 'Enable email notifications'
    },
    {
      name: 'dashboard_notifications',
      category: 'notification',
      value: true,
      dataType: 'boolean',
      description: 'Enable dashboard notifications'
    },
    
    // Integration configurations
    {
      name: 'sara_bot_url',
      category: 'integration',
      value: 'http://localhost:8000',
      dataType: 'string',
      description: 'Sara Bot API URL'
    },
    {
      name: 'webhook_url',
      category: 'integration',
      value: '',
      dataType: 'string',
      description: 'Webhook URL for call events'
    }
  ];
  
  for (const config of defaultConfigs) {
    const existingConfig = await this.findOne({ name: config.name });
    if (!existingConfig) {
      await this.create(config);
    }
  }
  
  console.log('✅ Default system configurations initialized');
};

module.exports = mongoose.model('SystemConfig', systemConfigSchema);
