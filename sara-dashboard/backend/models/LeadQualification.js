/**
 * LeadQualification Model
 * Database schema for storing BANT qualification data per call
 */

const mongoose = require('mongoose');

const leadQualificationSchema = new mongoose.Schema({
  callId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  budget: {
    amount: Number,
    currency: String,
    timeframe: String, // 'immediate', 'this_month', 'next_quarter', 'this_year'
    score: {
      type: Number,
      min: 0,
      max: 10,
      default: 0
    },
    notes: String
  },
  authority: {
    decisionMaker: {
      type: Boolean,
      default: false
    },
    influenceLevel: {
      type: String,
      enum: ['high', 'medium', 'low', 'unknown'],
      default: 'unknown'
    },
    approvalProcess: String,
    score: {
      type: Number,
      min: 0,
      max: 10,
      default: 0
    },
    notes: String
  },
  need: {
    painPoints: [String],
    currentSolution: String,
    urgencyLevel: {
      type: String,
      enum: ['critical', 'high', 'medium', 'low'],
      default: 'medium'
    },
    impactLevel: {
      type: String,
      enum: ['high', 'medium', 'low'],
      default: 'medium'
    },
    score: {
      type: Number,
      min: 0,
      max: 10,
      default: 0
    },
    notes: String
  },
  timeline: {
    decisionDate: Date,
    implementationDate: Date,
    urgency: {
      type: String,
      enum: ['immediate', 'urgent', 'this_month', 'next_quarter', 'flexible'],
      default: 'flexible'
    },
    score: {
      type: Number,
      min: 0,
      max: 10,
      default: 0
    },
    notes: String
  },
  qualificationScore: {
    type: Number,
    min: 0,
    max: 40, // Sum of all BANT scores
    default: 0,
    index: true
  },
  stage: {
    type: String,
    enum: ['initial', 'qualified', 'presentation', 'objection', 'closing', 'converted', 'lost'],
    default: 'initial',
    index: true
  },
  notes: String,
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
leadQualificationSchema.index({ callId: 1 }, { unique: true });
leadQualificationSchema.index({ qualificationScore: -1 });
leadQualificationSchema.index({ stage: 1 });
leadQualificationSchema.index({ createdAt: -1 });

// Pre-save middleware to calculate qualification score and update timestamp
leadQualificationSchema.pre('save', function(next) {
  this.qualificationScore = (this.budget.score || 0) + 
                           (this.authority.score || 0) + 
                           (this.need.score || 0) + 
                           (this.timeline.score || 0);
  this.updatedAt = new Date();
  next();
});

// Static method to get qualification by call ID
leadQualificationSchema.statics.getByCallId = async function(callId) {
  return await this.findOne({ callId });
};

// Static method to update qualification score
leadQualificationSchema.statics.updateScore = async function(callId, bantData) {
  const qualification = await this.findOne({ callId });
  if (qualification) {
    if (bantData.budget !== undefined) qualification.budget.score = bantData.budget;
    if (bantData.authority !== undefined) qualification.authority.score = bantData.authority;
    if (bantData.need !== undefined) qualification.need.score = bantData.need;
    if (bantData.timeline !== undefined) qualification.timeline.score = bantData.timeline;
    
    await qualification.save();
    return qualification;
  }
  return null;
};

// Static method to get qualification statistics
leadQualificationSchema.statics.getQualificationStats = async function(startDate, endDate) {
  const matchStage = {};
  
  if (startDate && endDate) {
    matchStage.createdAt = {
      $gte: new Date(startDate),
      $lte: new Date(endDate)
    };
  }
  
  const stats = await this.aggregate([
    { $match: matchStage },
    {
      $group: {
        _id: null,
        totalLeads: { $sum: 1 },
        averageScore: { $avg: '$qualificationScore' },
        qualifiedLeads: {
          $sum: { $cond: [{ $gte: ['$qualificationScore', 20] }, 1, 0] }
        },
        highQualifiedLeads: {
          $sum: { $cond: [{ $gte: ['$qualificationScore', 30] }, 1, 0] }
        },
        convertedLeads: {
          $sum: { $cond: [{ $eq: ['$stage', 'converted'] }, 1, 0] }
        }
      }
    }
  ]);
  
  return stats[0] || {
    totalLeads: 0,
    averageScore: 0,
    qualifiedLeads: 0,
    highQualifiedLeads: 0,
    convertedLeads: 0
  };
};

// Virtual for qualification level
leadQualificationSchema.virtual('qualificationLevel').get(function() {
  if (this.qualificationScore >= 30) return 'high';
  if (this.qualificationScore >= 20) return 'medium';
  if (this.qualificationScore >= 10) return 'low';
  return 'unqualified';
});

// Virtual for qualification summary
leadQualificationSchema.virtual('summary').get(function() {
  return {
    callId: this.callId,
    qualificationScore: this.qualificationScore,
    qualificationLevel: this.qualificationLevel,
    stage: this.stage,
    budget: this.budget.score,
    authority: this.authority.score,
    need: this.need.score,
    timeline: this.timeline.score
  };
});

module.exports = mongoose.model('LeadQualification', leadQualificationSchema);
