/**
 * WhatsAppMessage Model
 * Database schema for storing WhatsApp message logs and delivery status
 */

const mongoose = require('mongoose');

const whatsAppMessageSchema = new mongoose.Schema({
  // WhatsApp Message ID (from Meta API)
  messageId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  
  // Reference to the call that triggered this message
  callId: {
    type: String,
    ref: 'CallLog',
    index: true
  },
  
  // Recipient Information
  phone: {
    type: String,
    required: true,
    index: true
  },
  customerName: {
    type: String,
    default: 'Customer'
  },
  
  // Message Direction
  direction: {
    type: String,
    enum: ['outbound', 'inbound'],
    default: 'outbound',
    index: true
  },
  
  // Message Type
  type: {
    type: String,
    enum: ['text', 'template', 'payment_link', 'image', 'document', 'audio', 'video'],
    default: 'text',
    index: true
  },
  
  // Message Content
  content: {
    type: String,
    required: true
  },
  
  // Template Information (if template message)
  template: {
    name: String,
    language: String,
    components: mongoose.Schema.Types.Mixed
  },
  
  // Payment Link Reference (if payment_link type)
  paymentLinkId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'PaymentLink'
  },
  paymentLinkUrl: {
    type: String
  },
  
  // Delivery Status
  status: {
    type: String,
    enum: ['pending', 'sent', 'delivered', 'read', 'failed'],
    default: 'pending',
    index: true
  },
  
  // Status Timestamps
  sentAt: {
    type: Date
  },
  deliveredAt: {
    type: Date
  },
  readAt: {
    type: Date
  },
  failedAt: {
    type: Date
  },
  
  // Error Information
  error: {
    code: String,
    message: String,
    details: String,
    needsOptin: {
      type: Boolean,
      default: false
    }
  },
  
  // Metadata
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  
  // Timestamps
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  }
}, {
  timestamps: true,
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Indexes for better query performance
whatsAppMessageSchema.index({ status: 1, createdAt: -1 });
whatsAppMessageSchema.index({ type: 1, status: 1 });
whatsAppMessageSchema.index({ phone: 1, createdAt: -1 });
whatsAppMessageSchema.index({ direction: 1, createdAt: -1 });

// Virtual for message age
whatsAppMessageSchema.virtual('age').get(function() {
  const now = new Date();
  const diffMs = now - this.createdAt;
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
});

// Virtual for masked phone
whatsAppMessageSchema.virtual('maskedPhone').get(function() {
  if (!this.phone) return '';
  if (this.phone.length <= 4) return '****';
  return this.phone.slice(0, -4).replace(/./g, '*') + this.phone.slice(-4);
});

// Virtual for status badge color
whatsAppMessageSchema.virtual('statusColor').get(function() {
  switch (this.status) {
    case 'read': return 'blue';
    case 'delivered': return 'green';
    case 'sent': return 'yellow';
    case 'pending': return 'gray';
    case 'failed': return 'red';
    default: return 'gray';
  }
});

// Pre-save middleware
whatsAppMessageSchema.pre('save', function(next) {
  // Update status timestamps
  if (this.isModified('status')) {
    const now = new Date();
    switch (this.status) {
      case 'sent':
        if (!this.sentAt) this.sentAt = now;
        break;
      case 'delivered':
        if (!this.deliveredAt) this.deliveredAt = now;
        break;
      case 'read':
        if (!this.readAt) this.readAt = now;
        break;
      case 'failed':
        if (!this.failedAt) this.failedAt = now;
        break;
    }
  }
  
  next();
});

// Static method to get message statistics
whatsAppMessageSchema.statics.getMessageStats = async function(startDate, endDate) {
  const matchStage = { direction: 'outbound' };
  
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
        totalMessages: { $sum: 1 },
        sentMessages: {
          $sum: { $cond: [{ $in: ['$status', ['sent', 'delivered', 'read']] }, 1, 0] }
        },
        deliveredMessages: {
          $sum: { $cond: [{ $in: ['$status', ['delivered', 'read']] }, 1, 0] }
        },
        readMessages: {
          $sum: { $cond: [{ $eq: ['$status', 'read'] }, 1, 0] }
        },
        failedMessages: {
          $sum: { $cond: [{ $eq: ['$status', 'failed'] }, 1, 0] }
        },
        pendingMessages: {
          $sum: { $cond: [{ $eq: ['$status', 'pending'] }, 1, 0] }
        },
        paymentLinkMessages: {
          $sum: { $cond: [{ $eq: ['$type', 'payment_link'] }, 1, 0] }
        },
        optinRequiredCount: {
          $sum: { $cond: [{ $eq: ['$error.needsOptin', true] }, 1, 0] }
        }
      }
    }
  ]);
  
  const result = stats[0] || {
    totalMessages: 0,
    sentMessages: 0,
    deliveredMessages: 0,
    readMessages: 0,
    failedMessages: 0,
    pendingMessages: 0,
    paymentLinkMessages: 0,
    optinRequiredCount: 0
  };
  
  // Calculate rates
  result.deliveryRate = result.sentMessages > 0 
    ? ((result.deliveredMessages / result.sentMessages) * 100).toFixed(1)
    : 0;
  result.readRate = result.deliveredMessages > 0 
    ? ((result.readMessages / result.deliveredMessages) * 100).toFixed(1)
    : 0;
  result.failureRate = result.totalMessages > 0 
    ? ((result.failedMessages / result.totalMessages) * 100).toFixed(1)
    : 0;
  
  return result;
};

// Static method to get message type breakdown
whatsAppMessageSchema.statics.getTypeBreakdown = async function(days = 7) {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  
  return await this.aggregate([
    {
      $match: {
        createdAt: { $gte: startDate },
        direction: 'outbound'
      }
    },
    {
      $group: {
        _id: '$type',
        count: { $sum: 1 },
        delivered: {
          $sum: { $cond: [{ $in: ['$status', ['delivered', 'read']] }, 1, 0] }
        },
        failed: {
          $sum: { $cond: [{ $eq: ['$status', 'failed'] }, 1, 0] }
        }
      }
    },
    {
      $project: {
        type: '$_id',
        count: 1,
        delivered: 1,
        failed: 1,
        deliveryRate: {
          $cond: [
            { $gt: ['$count', 0] },
            { $multiply: [{ $divide: ['$delivered', '$count'] }, 100] },
            0
          ]
        }
      }
    },
    {
      $sort: { count: -1 }
    }
  ]);
};

// Static method to get daily message trends
whatsAppMessageSchema.statics.getDailyTrends = async function(days = 7) {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  startDate.setHours(0, 0, 0, 0);
  
  return await this.aggregate([
    {
      $match: {
        createdAt: { $gte: startDate },
        direction: 'outbound'
      }
    },
    {
      $group: {
        _id: {
          year: { $year: '$createdAt' },
          month: { $month: '$createdAt' },
          day: { $dayOfMonth: '$createdAt' }
        },
        totalMessages: { $sum: 1 },
        deliveredMessages: {
          $sum: { $cond: [{ $in: ['$status', ['delivered', 'read']] }, 1, 0] }
        },
        failedMessages: {
          $sum: { $cond: [{ $eq: ['$status', 'failed'] }, 1, 0] }
        },
        paymentLinks: {
          $sum: { $cond: [{ $eq: ['$type', 'payment_link'] }, 1, 0] }
        }
      }
    },
    {
      $sort: { '_id.year': 1, '_id.month': 1, '_id.day': 1 }
    }
  ]);
};

// Instance method to update delivery status
whatsAppMessageSchema.methods.updateDeliveryStatus = async function(newStatus, errorInfo = null) {
  this.status = newStatus;
  
  if (errorInfo) {
    this.error = {
      code: errorInfo.code,
      message: errorInfo.message,
      details: errorInfo.details,
      needsOptin: errorInfo.needsOptin || false
    };
  }
  
  return await this.save();
};

module.exports = mongoose.model('WhatsAppMessage', whatsAppMessageSchema);

