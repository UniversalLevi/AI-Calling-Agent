/**
 * SalesScript Model
 * Database schema for storing sales scripts and conversation flows
 */

const mongoose = require('mongoose');

const salesScriptSchema = new mongoose.Schema({
  productId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Product',
    required: true,
    index: true
  },
  scriptType: {
    type: String,
    required: true,
    enum: ['greeting', 'qualification', 'presentation', 'objection', 'closing', 'upsell'],
    index: true
  },
  technique: {
    type: String,
    required: true,
    enum: ['SPIN', 'Consultative', 'Challenger', 'Generic'],
    default: 'Generic'
  },
  stage: {
    type: String,
    required: true,
    enum: ['Situation', 'Problem', 'Implication', 'Need-payoff', 'Presentation', 'Closing'],
    default: 'Presentation'
  },
  content: {
    type: String,
    required: true,
    trim: true
  },
  language: {
    type: String,
    required: true,
    enum: ['en', 'hi', 'mixed'],
    default: 'en',
    index: true
  },
  priority: {
    type: Number,
    default: 1,
    min: 1,
    max: 10
  },
  conditions: {
    triggers: [String], // Keywords that trigger this script
    minQualificationScore: Number, // Minimum BANT score required
    maxCallDuration: Number, // Maximum call duration in seconds
    objectionsRequired: [String] // Objections that must be present
  },
  variables: [{
    name: String,
    type: String, // 'text', 'number', 'date', 'boolean'
    defaultValue: String,
    description: String
  }],
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
salesScriptSchema.index({ productId: 1, scriptType: 1, isActive: 1 });
salesScriptSchema.index({ technique: 1, stage: 1, isActive: 1 });
salesScriptSchema.index({ language: 1, isActive: 1 });
salesScriptSchema.index({ priority: -1, successRate: -1 });

// Pre-save middleware to update timestamp
salesScriptSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

// Static method to get scripts for a product and stage
salesScriptSchema.statics.getScriptsForStage = async function(productId, scriptType, language = 'en') {
  return await this.find({
    productId,
    scriptType,
    language,
    isActive: true
  }).sort({ priority: -1, successRate: -1 });
};

// Static method to get SPIN scripts for a product
salesScriptSchema.statics.getSPINScripts = async function(productId, language = 'en') {
  return await this.find({
    productId,
    technique: 'SPIN',
    language,
    isActive: true
  }).sort({ stage: 1, priority: -1 });
};

// Static method to get scripts by technique
salesScriptSchema.statics.getScriptsByTechnique = async function(productId, technique, language = 'en') {
  return await this.find({
    productId,
    technique,
    language,
    isActive: true
  }).sort({ priority: -1, successRate: -1 });
};

// Static method to update success rate
salesScriptSchema.statics.updateSuccessRate = async function(scriptId, success) {
  const script = await this.findById(scriptId);
  if (script) {
    script.usageCount += 1;
    // Simple moving average for success rate
    const currentRate = script.successRate;
    const newRate = ((currentRate * (script.usageCount - 1)) + (success ? 100 : 0)) / script.usageCount;
    script.successRate = Math.round(newRate);
    await script.save();
  }
};

// Virtual for script summary
salesScriptSchema.virtual('summary').get(function() {
  return {
    id: this._id,
    scriptType: this.scriptType,
    technique: this.technique,
    stage: this.stage,
    language: this.language,
    priority: this.priority,
    successRate: this.successRate,
    usageCount: this.usageCount
  };
});

module.exports = mongoose.model('SalesScript', salesScriptSchema);
