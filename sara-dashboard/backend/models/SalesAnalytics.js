/**
 * SalesAnalytics Model
 * Database schema for storing detailed sales metrics per call
 */

const mongoose = require('mongoose');

const salesAnalyticsSchema = new mongoose.Schema({
  callId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  conversionStage: {
    type: String,
    enum: ['greeting', 'qualification', 'presentation', 'objection', 'closing', 'converted', 'lost'],
    required: true,
    index: true
  },
  objectionsFaced: [{
    objectionType: String,
    timestamp: Date,
    resolved: Boolean,
    resolutionTime: Number, // seconds
    techniqueUsed: String
  }],
  techniquesUsed: [{
    technique: String,
    stage: String,
    timestamp: Date,
    success: Boolean
  }],
  sentimentScore: {
    type: Number,
    min: -1,
    max: 1,
    default: 0
  },
  sentimentHistory: [{
    timestamp: Date,
    score: Number,
    text: String
  }],
  talkListenRatio: {
    aiTalkTime: Number, // seconds
    userTalkTime: Number, // seconds
    ratio: Number, // AI talk percentage
    targetRatio: {
      type: Number,
      default: 0.4 // 40% AI, 60% user
    }
  },
  keyPhrases: [{
    phrase: String,
    category: String, // 'buying_signal', 'objection', 'urgency', 'interest'
    timestamp: Date,
    context: String
  }],
  outcomeType: {
    type: String,
    enum: ['converted', 'not_interested', 'callback', 'follow_up', 'objection_unresolved', 'no_answer'],
    required: true,
    index: true
  },
  callQuality: {
    score: {
      type: Number,
      min: 0,
      max: 100,
      default: 0
    },
    factors: {
      talkListenRatio: Number,
      sentimentTrend: Number,
      stageCompletion: Number,
      objectionResolution: Number
    }
  },
  duration: {
    type: Number, // total call duration in seconds
    required: true
  },
  stageTimings: [{
    stage: String,
    startTime: Date,
    endTime: Date,
    duration: Number
  }],
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
salesAnalyticsSchema.index({ callId: 1 }, { unique: true });
salesAnalyticsSchema.index({ conversionStage: 1, createdAt: -1 });
salesAnalyticsSchema.index({ outcomeType: 1, createdAt: -1 });
salesAnalyticsSchema.index({ 'objectionsFaced.objectionType': 1 });
salesAnalyticsSchema.index({ 'techniquesUsed.technique': 1 });

// Pre-save middleware to calculate call quality and update timestamp
salesAnalyticsSchema.pre('save', function(next) {
  // Calculate talk-listen ratio
  if (this.talkListenRatio.aiTalkTime && this.talkListenRatio.userTalkTime) {
    const totalTime = this.talkListenRatio.aiTalkTime + this.talkListenRatio.userTalkTime;
    this.talkListenRatio.ratio = this.talkListenRatio.aiTalkTime / totalTime;
  }
  
  // Calculate call quality score
  this.callQuality.score = this.calculateCallQuality();
  
  this.updatedAt = new Date();
  next();
});

// Method to calculate call quality score
salesAnalyticsSchema.methods.calculateCallQuality = function() {
  let score = 0;
  
  // Talk-listen ratio score (25 points)
  const ratioDiff = Math.abs(this.talkListenRatio.ratio - this.talkListenRatio.targetRatio);
  const ratioScore = Math.max(0, 25 - (ratioDiff * 100));
  score += ratioScore;
  
  // Sentiment trend score (25 points)
  if (this.sentimentHistory.length > 1) {
    const firstSentiment = this.sentimentHistory[0].score;
    const lastSentiment = this.sentimentHistory[this.sentimentHistory.length - 1].score;
    const sentimentImprovement = lastSentiment - firstSentiment;
    score += Math.max(0, 25 + (sentimentImprovement * 25));
  } else {
    score += 25; // Default if no history
  }
  
  // Stage completion score (25 points)
  const completedStages = this.stageTimings.length;
  const totalStages = 6; // greeting, qualification, presentation, objection, closing, converted
  const completionScore = (completedStages / totalStages) * 25;
  score += completionScore;
  
  // Objection resolution score (25 points)
  if (this.objectionsFaced.length > 0) {
    const resolvedObjections = this.objectionsFaced.filter(obj => obj.resolved).length;
    const resolutionScore = (resolvedObjections / this.objectionsFaced.length) * 25;
    score += resolutionScore;
  } else {
    score += 25; // No objections is good
  }
  
  return Math.round(Math.min(100, Math.max(0, score)));
};

// Static method to get analytics by call ID
salesAnalyticsSchema.statics.getByCallId = async function(callId) {
  return await this.findOne({ callId });
};

// Static method to get conversion funnel data
salesAnalyticsSchema.statics.getConversionFunnel = async function(startDate, endDate) {
  const matchStage = {};
  
  if (startDate && endDate) {
    matchStage.createdAt = {
      $gte: new Date(startDate),
      $lte: new Date(endDate)
    };
  }
  
  const funnelData = await this.aggregate([
    { $match: matchStage },
    {
      $group: {
        _id: '$conversionStage',
        count: { $sum: 1 },
        averageDuration: { $avg: '$duration' },
        averageQuality: { $avg: '$callQuality.score' }
      }
    },
    {
      $sort: { _id: 1 }
    }
  ]);
  
  return funnelData;
};

// Static method to get objection analysis
salesAnalyticsSchema.statics.getObjectionAnalysis = async function(startDate, endDate) {
  const matchStage = {};
  
  if (startDate && endDate) {
    matchStage.createdAt = {
      $gte: new Date(startDate),
      $lte: new Date(endDate)
    };
  }
  
  const objectionData = await this.aggregate([
    { $match: matchStage },
    { $unwind: '$objectionsFaced' },
    {
      $group: {
        _id: '$objectionsFaced.objectionType',
        count: { $sum: 1 },
        resolvedCount: {
          $sum: { $cond: ['$objectionsFaced.resolved', 1, 0] }
        },
        averageResolutionTime: { $avg: '$objectionsFaced.resolutionTime' }
      }
    },
    {
      $addFields: {
        resolutionRate: {
          $multiply: [
            { $divide: ['$resolvedCount', '$count'] },
            100
          ]
        }
      }
    },
    {
      $sort: { count: -1 }
    }
  ]);
  
  return objectionData;
};

// Static method to get technique performance
salesAnalyticsSchema.statics.getTechniquePerformance = async function(startDate, endDate) {
  const matchStage = {};
  
  if (startDate && endDate) {
    matchStage.createdAt = {
      $gte: new Date(startDate),
      $lte: new Date(endDate)
    };
  }
  
  const techniqueData = await this.aggregate([
    { $match: matchStage },
    { $unwind: '$techniquesUsed' },
    {
      $group: {
        _id: '$techniquesUsed.technique',
        count: { $sum: 1 },
        successCount: {
          $sum: { $cond: ['$techniquesUsed.success', 1, 0] }
        },
        stages: { $addToSet: '$techniquesUsed.stage' }
      }
    },
    {
      $addFields: {
        successRate: {
          $multiply: [
            { $divide: ['$successCount', '$count'] },
            100
          ]
        }
      }
    },
    {
      $sort: { successRate: -1 }
    }
  ]);
  
  return techniqueData;
};

// Virtual for analytics summary
salesAnalyticsSchema.virtual('summary').get(function() {
  return {
    callId: this.callId,
    conversionStage: this.conversionStage,
    outcomeType: this.outcomeType,
    callQuality: this.callQuality.score,
    duration: this.duration,
    objectionsCount: this.objectionsFaced.length,
    techniquesUsed: this.techniquesUsed.length,
    sentimentScore: this.sentimentScore,
    talkListenRatio: this.talkListenRatio.ratio
  };
});

module.exports = mongoose.model('SalesAnalytics', salesAnalyticsSchema);
