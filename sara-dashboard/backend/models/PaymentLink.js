/**
 * PaymentLink Model
 * Database schema for storing payment links and tracking their status
 */

const mongoose = require('mongoose');

const paymentLinkSchema = new mongoose.Schema({
  // Razorpay Payment Link ID
  razorpayLinkId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  
  // Reference to the call that triggered this payment
  callId: {
    type: String,
    ref: 'CallLog',
    index: true
  },
  
  // Customer Information
  phone: {
    type: String,
    required: true,
    index: true
  },
  customerName: {
    type: String,
    default: 'Customer'
  },
  
  // Payment Details
  amount: {
    type: Number,
    required: true // Amount in paise
  },
  amountDisplay: {
    type: Number // Amount in rupees for display
  },
  currency: {
    type: String,
    default: 'INR'
  },
  
  // Product Information
  productName: {
    type: String,
    required: true
  },
  productId: {
    type: String,
    index: true
  },
  
  // Payment Link Details
  shortUrl: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  },
  
  // Status Tracking
  status: {
    type: String,
    enum: ['created', 'sent', 'viewed', 'paid', 'expired', 'cancelled', 'failed'],
    default: 'created',
    index: true
  },
  
  // WhatsApp Message Reference
  whatsappMessageId: {
    type: String,
    index: true
  },
  whatsappStatus: {
    type: String,
    enum: ['pending', 'sent', 'delivered', 'read', 'failed'],
    default: 'pending'
  },
  
  // Timestamps
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  },
  sentAt: {
    type: Date
  },
  viewedAt: {
    type: Date
  },
  paidAt: {
    type: Date
  },
  expiresAt: {
    type: Date
  },
  
  // Payment Completion Details
  paymentId: {
    type: String // Razorpay payment ID after successful payment
  },
  paymentMethod: {
    type: String // UPI, card, netbanking, etc.
  },
  
  // Error Tracking
  error: {
    code: String,
    message: String,
    occurredAt: Date
  },
  
  // Metadata
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  }
}, {
  timestamps: true,
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Indexes for better query performance
paymentLinkSchema.index({ status: 1, createdAt: -1 });
paymentLinkSchema.index({ phone: 1, createdAt: -1 });
paymentLinkSchema.index({ productId: 1, status: 1 });
paymentLinkSchema.index({ paidAt: -1 });

// Virtual for formatted amount
paymentLinkSchema.virtual('formattedAmount').get(function() {
  const amountInRupees = this.amountDisplay || (this.amount / 100);
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: this.currency || 'INR'
  }).format(amountInRupees);
});

// Virtual for payment age
paymentLinkSchema.virtual('age').get(function() {
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

// Virtual for is expired
paymentLinkSchema.virtual('isExpired').get(function() {
  if (this.status === 'paid') return false;
  if (!this.expiresAt) return false;
  return new Date() > this.expiresAt;
});

// Pre-save middleware
paymentLinkSchema.pre('save', function(next) {
  // Calculate display amount
  if (this.amount && !this.amountDisplay) {
    this.amountDisplay = this.amount / 100;
  }
  
  // Update status timestamps
  if (this.isModified('status')) {
    switch (this.status) {
      case 'sent':
        if (!this.sentAt) this.sentAt = new Date();
        break;
      case 'viewed':
        if (!this.viewedAt) this.viewedAt = new Date();
        break;
      case 'paid':
        if (!this.paidAt) this.paidAt = new Date();
        break;
    }
  }
  
  next();
});

// Static method to get payment statistics
paymentLinkSchema.statics.getPaymentStats = async function(startDate, endDate) {
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
        totalLinks: { $sum: 1 },
        paidLinks: {
          $sum: { $cond: [{ $eq: ['$status', 'paid'] }, 1, 0] }
        },
        pendingLinks: {
          $sum: { $cond: [{ $in: ['$status', ['created', 'sent', 'viewed']] }, 1, 0] }
        },
        failedLinks: {
          $sum: { $cond: [{ $in: ['$status', ['failed', 'expired', 'cancelled']] }, 1, 0] }
        },
        totalRevenue: {
          $sum: { $cond: [{ $eq: ['$status', 'paid'] }, '$amountDisplay', 0] }
        },
        pendingAmount: {
          $sum: { $cond: [{ $in: ['$status', ['created', 'sent', 'viewed']] }, '$amountDisplay', 0] }
        },
        averageAmount: { $avg: '$amountDisplay' }
      }
    }
  ]);
  
  const result = stats[0] || {
    totalLinks: 0,
    paidLinks: 0,
    pendingLinks: 0,
    failedLinks: 0,
    totalRevenue: 0,
    pendingAmount: 0,
    averageAmount: 0
  };
  
  // Calculate conversion rate
  result.conversionRate = result.totalLinks > 0 
    ? ((result.paidLinks / result.totalLinks) * 100).toFixed(1)
    : 0;
  
  return result;
};

// Static method to get daily revenue trends
paymentLinkSchema.statics.getDailyRevenue = async function(days = 7) {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  startDate.setHours(0, 0, 0, 0);
  
  return await this.aggregate([
    {
      $match: {
        status: 'paid',
        paidAt: { $gte: startDate }
      }
    },
    {
      $group: {
        _id: {
          year: { $year: '$paidAt' },
          month: { $month: '$paidAt' },
          day: { $dayOfMonth: '$paidAt' }
        },
        revenue: { $sum: '$amountDisplay' },
        count: { $sum: 1 }
      }
    },
    {
      $sort: { '_id.year': 1, '_id.month': 1, '_id.day': 1 }
    }
  ]);
};

// Static method to get product-wise payment stats
paymentLinkSchema.statics.getProductStats = async function() {
  return await this.aggregate([
    {
      $group: {
        _id: '$productName',
        totalLinks: { $sum: 1 },
        paidLinks: {
          $sum: { $cond: [{ $eq: ['$status', 'paid'] }, 1, 0] }
        },
        revenue: {
          $sum: { $cond: [{ $eq: ['$status', 'paid'] }, '$amountDisplay', 0] }
        }
      }
    },
    {
      $project: {
        productName: '$_id',
        totalLinks: 1,
        paidLinks: 1,
        revenue: 1,
        conversionRate: {
          $cond: [
            { $gt: ['$totalLinks', 0] },
            { $multiply: [{ $divide: ['$paidLinks', '$totalLinks'] }, 100] },
            0
          ]
        }
      }
    },
    {
      $sort: { revenue: -1 }
    }
  ]);
};

// Instance method to mark as sent
paymentLinkSchema.methods.markAsSent = async function(whatsappMessageId) {
  this.status = 'sent';
  this.sentAt = new Date();
  if (whatsappMessageId) {
    this.whatsappMessageId = whatsappMessageId;
    this.whatsappStatus = 'sent';
  }
  return await this.save();
};

// Instance method to mark as paid
paymentLinkSchema.methods.markAsPaid = async function(paymentId, paymentMethod) {
  this.status = 'paid';
  this.paidAt = new Date();
  if (paymentId) this.paymentId = paymentId;
  if (paymentMethod) this.paymentMethod = paymentMethod;
  return await this.save();
};

module.exports = mongoose.model('PaymentLink', paymentLinkSchema);

