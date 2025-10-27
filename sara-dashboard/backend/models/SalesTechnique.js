/**
 * SalesTechnique Model
 * Database schema for storing sales methodology configurations
 */

const mongoose = require('mongoose');

const salesTechniqueSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true,
    unique: true
  },
  type: {
    type: String,
    required: true,
    enum: ['SPIN', 'Consultative', 'Challenger', 'Generic'],
    index: true
  },
  description: {
    type: String,
    required: true,
    trim: true
  },
  stage: {
    type: String,
    required: true,
    enum: ['greeting', 'qualification', 'presentation', 'objection', 'closing', 'followup'],
    index: true
  },
  questions: [{
    question: String,
    purpose: String, // 'situation', 'problem', 'implication', 'need-payoff'
    expectedResponse: String,
    followUp: String
  }],
  responses: [{
    trigger: String, // Keywords that trigger this response
    response: String,
    technique: String // 'empathy', 'value', 'urgency', 'social_proof'
  }],
  triggers: [{
    keyword: String,
    context: String, // When to use this trigger
    action: String // What to do when triggered
  }],
  language: {
    type: String,
    required: true,
    enum: ['en', 'hi', 'mixed'],
    default: 'en',
    index: true
  },
  isActive: {
    type: Boolean,
    default: true,
    index: true
  },
  priority: {
    type: Number,
    default: 1,
    min: 1,
    max: 10
  },
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
salesTechniqueSchema.index({ type: 1, stage: 1, isActive: 1 });
salesTechniqueSchema.index({ language: 1, isActive: 1 });
salesTechniqueSchema.index({ priority: -1, successRate: -1 });

// Pre-save middleware to update timestamp
salesTechniqueSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

// Static method to get techniques by type and stage
salesTechniqueSchema.statics.getTechniquesByStage = async function(type, stage, language = 'en') {
  return await this.find({
    type,
    stage,
    language,
    isActive: true
  }).sort({ priority: -1, successRate: -1 });
};

// Static method to get SPIN techniques
salesTechniqueSchema.statics.getSPINTechniques = async function(language = 'en') {
  return await this.find({
    type: 'SPIN',
    language,
    isActive: true
  }).sort({ stage: 1, priority: -1 });
};

// Static method to get Consultative techniques
salesTechniqueSchema.statics.getConsultativeTechniques = async function(language = 'en') {
  return await this.find({
    type: 'Consultative',
    language,
    isActive: true
  }).sort({ priority: -1, successRate: -1 });
};

// Static method to get Challenger techniques
salesTechniqueSchema.statics.getChallengerTechniques = async function(language = 'en') {
  return await this.find({
    type: 'Challenger',
    language,
    isActive: true
  }).sort({ priority: -1, successRate: -1 });
};

// Static method to update success rate
salesTechniqueSchema.statics.updateSuccessRate = async function(techniqueId, success) {
  const technique = await this.findById(techniqueId);
  if (technique) {
    technique.usageCount += 1;
    // Simple moving average for success rate
    const currentRate = technique.successRate;
    const newRate = ((currentRate * (technique.usageCount - 1)) + (success ? 100 : 0)) / technique.usageCount;
    technique.successRate = Math.round(newRate);
    await technique.save();
  }
};

// Virtual for technique summary
salesTechniqueSchema.virtual('summary').get(function() {
  return {
    id: this._id,
    name: this.name,
    type: this.type,
    stage: this.stage,
    language: this.language,
    priority: this.priority,
    successRate: this.successRate,
    usageCount: this.usageCount
  };
});

module.exports = mongoose.model('SalesTechnique', salesTechniqueSchema);
