/**
 * CallLog Model
 * Database schema for storing call logs and analytics
 */

const mongoose = require('mongoose');

const callLogSchema = new mongoose.Schema({
  callId: {
    type: String,
    required: true
  },
  type: {
    type: String,
    enum: ['inbound', 'outbound'],
    required: true
  },
  caller: {
    type: String,
    required: true
  },
  receiver: {
    type: String,
    required: true
  },
  startTime: {
    type: Date,
    required: true,
    index: true
  },
  endTime: {
    type: Date,
    default: null
  },
  duration: {
    type: Number, // in seconds
    default: 0
  },
  status: {
    type: String,
    enum: ['success', 'failed', 'missed', 'in-progress'],
    default: 'in-progress',
    index: true
  },
  transcript: {
    type: String,
    default: ''
  },
  audioFile: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    enum: ['en', 'hi', 'mixed'],
    default: 'en'
  },
  interruptionCount: {
    type: Number,
    default: 0
  },
  satisfaction: {
    type: String,
    enum: ['positive', 'negative', 'neutral', 'unknown'],
    default: 'unknown'
  },
  metadata: {
    userAgent: String,
    ipAddress: String,
    location: String,
    deviceType: String
  },
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Indexes for better query performance
callLogSchema.index({ callId: 1 }, { unique: true });
callLogSchema.index({ caller: 1, createdAt: -1 });
callLogSchema.index({ receiver: 1, createdAt: -1 });
callLogSchema.index({ status: 1, createdAt: -1 });
callLogSchema.index({ type: 1, createdAt: -1 });

// Virtual for formatted duration
callLogSchema.virtual('formattedDuration').get(function() {
  if (!this.duration) return '00:00';
  
  const minutes = Math.floor(this.duration / 60);
  const seconds = this.duration % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
});

// Virtual for call age
callLogSchema.virtual('callAge').get(function() {
  if (!this.endTime) return null;
  
  const now = new Date();
  const diffMs = now - this.endTime;
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minutes ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hours ago`;
  
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} days ago`;
});

// Pre-save middleware to calculate duration
callLogSchema.pre('save', function(next) {
  if (this.endTime && this.startTime) {
    this.duration = Math.floor((this.endTime - this.startTime) / 1000);
  }
  this.updatedAt = new Date();
  next();
});

// Static method to get call statistics
callLogSchema.statics.getCallStats = async function(startDate, endDate) {
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
        totalCalls: { $sum: 1 },
        successfulCalls: {
          $sum: { $cond: [{ $eq: ['$status', 'success'] }, 1, 0] }
        },
        failedCalls: {
          $sum: { $cond: [{ $eq: ['$status', 'failed'] }, 1, 0] }
        },
        missedCalls: {
          $sum: { $cond: [{ $eq: ['$status', 'missed'] }, 1, 0] }
        },
        averageDuration: { $avg: '$duration' },
        totalDuration: { $sum: '$duration' }
      }
    }
  ]);
  
  return stats[0] || {
    totalCalls: 0,
    successfulCalls: 0,
    failedCalls: 0,
    missedCalls: 0,
    averageDuration: 0,
    totalDuration: 0
  };
};

// Static method to get daily call trends
callLogSchema.statics.getDailyTrends = async function(days = 7) {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  
  return await this.aggregate([
    {
      $match: {
        createdAt: { $gte: startDate }
      }
    },
    {
      $group: {
        _id: {
          year: { $year: '$createdAt' },
          month: { $month: '$createdAt' },
          day: { $dayOfMonth: '$createdAt' }
        },
        totalCalls: { $sum: 1 },
        successfulCalls: {
          $sum: { $cond: [{ $eq: ['$status', 'success'] }, 1, 0] }
        },
        failedCalls: {
          $sum: { $cond: [{ $eq: ['$status', 'failed'] }, 1, 0] }
        }
      }
    },
    {
      $sort: { '_id.year': 1, '_id.month': 1, '_id.day': 1 }
    }
  ]);
};

module.exports = mongoose.model('CallLog', callLogSchema);
