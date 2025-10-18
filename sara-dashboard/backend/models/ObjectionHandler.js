/**
 * ObjectionHandler Model
 * Database schema for storing objection responses by type
 */

const mongoose = require('mongoose');

const objectionHandlerSchema = new mongoose.Schema({
  objectionType: {
    type: String,
    required: true,
    enum: ['price', 'timing', 'competition', 'trust', 'authority', 'need', 'budget', 'urgency', 'other'],
    index: true
  },
  keywords: [String], // Keywords that indicate this objection
  response: {
    type: String,
    required: true,
    trim: true
  },
  technique: {
    type: String,
    required: true,
    enum: ['empathy_reframe', 'value_reinforcement', 'social_proof', 'urgency', 'alternative', 'question'],
    default: 'empathy_reframe'
  },
  language: {
    type: String,
    required: true,
    enum: ['en', 'hi', 'mixed'],
    default: 'en',
    index: true
  },
  followUpQuestions: [String], // Questions to ask after handling objection
  successRate: {
    type: Number,
    default: 0,
    min: 0,
    max: 100
  },
  usageCount: {
    type: Number,
    default: 0
  },
  priority: {
    type: Number,
    default: 1,
    min: 1,
    max: 10
  },
  isActive: {
    type: Boolean,
    default: true,
    index: true
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

// Indexes for better query performance
objectionHandlerSchema.index({ objectionType: 1, language: 1, isActive: 1 });
objectionHandlerSchema.index({ technique: 1, isActive: 1 });
objectionHandlerSchema.index({ priority: -1, successRate: -1 });

// Pre-save middleware to update timestamp
objectionHandlerSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

// Static method to get objection handlers by type
objectionHandlerSchema.statics.getHandlersByType = async function(objectionType, language = 'en') {
  return await this.find({
    objectionType,
    language,
    isActive: true
  }).sort({ priority: -1, successRate: -1 });
};

// Static method to detect objection type from user input
objectionHandlerSchema.statics.detectObjectionType = async function(userInput, language = 'en') {
  const userLower = userInput.toLowerCase();
  
  // Define objection keywords for each type
  const objectionKeywords = {
    price: ['expensive', 'cost', 'price', 'budget', 'cheap', 'afford', 'mahanga', 'paisa', 'costly'],
    timing: ['later', 'think', 'decide', 'time', 'busy', 'baad mein', 'soch', 'time', 'busy'],
    competition: ['already have', 'other company', 'competitor', 'alternative', 'different', 'pehle se', 'dusra'],
    trust: ['trust', 'believe', 'sure', 'confident', 'reliable', 'bharosa', 'yakeen', 'reliable'],
    authority: ['boss', 'manager', 'decision', 'approve', 'permission', 'boss', 'manager', 'decision'],
    need: ['need', 'want', 'require', 'necessary', 'important', 'zaroorat', 'chahiye', 'important'],
    budget: ['budget', 'money', 'funds', 'financial', 'paisa', 'budget', 'money'],
    urgency: ['urgent', 'immediate', 'quick', 'fast', 'jaldi', 'urgent', 'immediate']
  };
  
  // Find matching objection types
  const matchedTypes = [];
  for (const [type, keywords] of Object.entries(objectionKeywords)) {
    if (keywords.some(keyword => userLower.includes(keyword))) {
      matchedTypes.push(type);
    }
  }
  
  return matchedTypes;
};

// Static method to get best objection handler
objectionHandlerSchema.statics.getBestHandler = async function(objectionType, language = 'en') {
  return await this.findOne({
    objectionType,
    language,
    isActive: true
  }).sort({ priority: -1, successRate: -1 });
};

// Static method to update success rate
objectionHandlerSchema.statics.updateSuccessRate = async function(handlerId, success) {
  const handler = await this.findById(handlerId);
  if (handler) {
    handler.usageCount += 1;
    // Simple moving average for success rate
    const currentRate = handler.successRate;
    const newRate = ((currentRate * (handler.usageCount - 1)) + (success ? 100 : 0)) / handler.usageCount;
    handler.successRate = Math.round(newRate);
    await handler.save();
  }
};

// Virtual for handler summary
objectionHandlerSchema.virtual('summary').get(function() {
  return {
    id: this._id,
    objectionType: this.objectionType,
    technique: this.technique,
    language: this.language,
    priority: this.priority,
    successRate: this.successRate,
    usageCount: this.usageCount
  };
});

module.exports = mongoose.model('ObjectionHandler', objectionHandlerSchema);
