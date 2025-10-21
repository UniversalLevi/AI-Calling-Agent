/**
 * AIDA Product Model
 * Database schema for AIDA sales framework products
 */

const mongoose = require('mongoose');

const aidaProductSchema = new mongoose.Schema({
  // Basic Product Information
  brand_name: {
    type: String,
    required: true,
    trim: true,
    maxlength: 100
  },
  product_name: {
    type: String,
    required: true,
    trim: true,
    maxlength: 200
  },
  category: {
    type: String,
    required: true,
    enum: ['travel', 'food', 'service', 'electronics', 'healthcare', 'education', 'finance', 'other'],
    default: 'service'
  },
  product_type: {
    type: String,
    required: true,
    enum: ['low', 'medium', 'high'],
    default: 'medium'
  },
  offer_tagline: {
    type: String,
    required: true,
    trim: true,
    maxlength: 300
  },
  
  // Product Details
  features: [{
    type: String,
    trim: true,
    maxlength: 200
  }],
  benefits: [{
    type: String,
    trim: true,
    maxlength: 200
  }],
  
  // AIDA Framework Content
  emotion_tone: {
    type: String,
    required: true,
    enum: ['friendly', 'trustworthy', 'luxury', 'professional', 'casual', 'urgent'],
    default: 'friendly'
  },
  call_to_action: {
    type: String,
    required: true,
    trim: true,
    maxlength: 100
  },
  
  // AIDA Stage-Specific Content
  attention_hooks: [{
    type: String,
    trim: true,
    maxlength: 200
  }],
  interest_questions: [{
    type: String,
    trim: true,
    maxlength: 300
  }],
  desire_statements: [{
    type: String,
    trim: true,
    maxlength: 300
  }],
  action_prompts: [{
    type: String,
    trim: true,
    maxlength: 200
  }],
  
  // Objection Handling
  objection_responses: {
    price: [{
      type: String,
      trim: true,
      maxlength: 300
    }],
    timing: [{
      type: String,
      trim: true,
      maxlength: 300
    }],
    authority: [{
      type: String,
      trim: true,
      maxlength: 300
    }],
    need: [{
      type: String,
      trim: true,
      maxlength: 300
    }],
    competition: [{
      type: String,
      trim: true,
      maxlength: 300
    }],
    disinterest: [{
      type: String,
      trim: true,
      maxlength: 300
    }]
  },
  
  // Product Status
  isActive: {
    type: Boolean,
    default: false
  },
  isPublished: {
    type: Boolean,
    default: false
  },
  
  // Analytics and Performance
  analytics: {
    total_calls: {
      type: Number,
      default: 0
    },
    conversions: {
      type: Number,
      default: 0
    },
    conversion_rate: {
      type: Number,
      default: 0
    },
    avg_call_duration: {
      type: Number,
      default: 0
    },
    stage_completion_rates: {
      attention: { type: Number, default: 0 },
      interest: { type: Number, default: 0 },
      desire: { type: Number, default: 0 },
      action: { type: Number, default: 0 }
    },
    objection_frequency: {
      price: { type: Number, default: 0 },
      timing: { type: Number, default: 0 },
      authority: { type: Number, default: 0 },
      need: { type: Number, default: 0 },
      competition: { type: Number, default: 0 },
      disinterest: { type: Number, default: 0 }
    }
  },
  
  // Metadata
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  lastModifiedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  tags: [{
    type: String,
    trim: true,
    maxlength: 50
  }],
  description: {
    type: String,
    trim: true,
    maxlength: 1000
  },
  
  // Timestamps
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true,
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Indexes
aidaProductSchema.index({ brand_name: 1, product_name: 1 });
aidaProductSchema.index({ category: 1 });
aidaProductSchema.index({ product_type: 1 });
aidaProductSchema.index({ isActive: 1 });
aidaProductSchema.index({ isPublished: 1 });
aidaProductSchema.index({ createdAt: -1 });

// Virtual for conversion rate calculation
aidaProductSchema.virtual('calculatedConversionRate').get(function() {
  if (this.analytics.total_calls > 0) {
    return (this.analytics.conversions / this.analytics.total_calls) * 100;
  }
  return 0;
});

// Virtual for product summary
aidaProductSchema.virtual('summary').get(function() {
  return {
    id: this._id,
    name: this.product_name,
    brand: this.brand_name,
    category: this.category,
    type: this.product_type,
    isActive: this.isActive,
    conversionRate: this.calculatedConversionRate,
    totalCalls: this.analytics.total_calls
  };
});

// Pre-save middleware to update analytics
aidaProductSchema.pre('save', function(next) {
  // Update conversion rate
  if (this.analytics.total_calls > 0) {
    this.analytics.conversion_rate = (this.analytics.conversions / this.analytics.total_calls) * 100;
  }
  
  // Update timestamp
  this.updatedAt = new Date();
  
  next();
});

// Static method to get active product
aidaProductSchema.statics.getActiveProduct = async function() {
  try {
    const activeProduct = await this.findOne({ isActive: true }).populate('createdBy', 'username email');
    return activeProduct;
  } catch (error) {
    throw new Error(`Error fetching active product: ${error.message}`);
  }
};

// Static method to set active product
aidaProductSchema.statics.setActiveProduct = async function(productId) {
  try {
    // First, deactivate all products
    await this.updateMany({}, { isActive: false });
    
    // Then activate the specified product
    const product = await this.findByIdAndUpdate(
      productId,
      { isActive: true },
      { new: true }
    ).populate('createdBy', 'username email');
    
    if (!product) {
      throw new Error('Product not found');
    }
    
    return product;
  } catch (error) {
    throw new Error(`Error setting active product: ${error.message}`);
  }
};

// Static method to get products by category
aidaProductSchema.statics.getByCategory = async function(category) {
  try {
    const products = await this.find({ category }).sort({ createdAt: -1 });
    return products;
  } catch (error) {
    throw new Error(`Error fetching products by category: ${error.message}`);
  }
};

// Static method to get product performance stats
aidaProductSchema.statics.getPerformanceStats = async function() {
  try {
    const stats = await this.aggregate([
      {
        $group: {
          _id: null,
          totalProducts: { $sum: 1 },
          activeProducts: { $sum: { $cond: ['$isActive', 1, 0] } },
          totalCalls: { $sum: '$analytics.total_calls' },
          totalConversions: { $sum: '$analytics.conversions' },
          avgConversionRate: { $avg: '$analytics.conversion_rate' },
          avgCallDuration: { $avg: '$analytics.avg_call_duration' }
        }
      }
    ]);
    
    return stats[0] || {
      totalProducts: 0,
      activeProducts: 0,
      totalCalls: 0,
      totalConversions: 0,
      avgConversionRate: 0,
      avgCallDuration: 0
    };
  } catch (error) {
    throw new Error(`Error fetching performance stats: ${error.message}`);
  }
};

// Instance method to update analytics
aidaProductSchema.methods.updateAnalytics = async function(callData) {
  try {
    this.analytics.total_calls += 1;
    
    if (callData.converted) {
      this.analytics.conversions += 1;
    }
    
    if (callData.duration) {
      const currentAvg = this.analytics.avg_call_duration;
      const totalCalls = this.analytics.total_calls;
      this.analytics.avg_call_duration = ((currentAvg * (totalCalls - 1)) + callData.duration) / totalCalls;
    }
    
    // Update stage completion rates
    if (callData.stagesReached) {
      for (const stage of callData.stagesReached) {
        if (this.analytics.stage_completion_rates[stage] !== undefined) {
          this.analytics.stage_completion_rates[stage] += 1;
        }
      }
    }
    
    // Update objection frequency
    if (callData.objections) {
      for (const objection of callData.objections) {
        if (this.analytics.objection_frequency[objection] !== undefined) {
          this.analytics.objection_frequency[objection] += 1;
        }
      }
    }
    
    await this.save();
    return this;
  } catch (error) {
    throw new Error(`Error updating analytics: ${error.message}`);
  }
};

// Instance method to get AIDA content for stage
aidaProductSchema.methods.getStageContent = function(stage) {
  const stageContent = {
    attention: {
      hooks: this.attention_hooks,
      tagline: this.offer_tagline,
      brand: this.brand_name,
      product: this.product_name
    },
    interest: {
      questions: this.interest_questions,
      features: this.features,
      category: this.category
    },
    desire: {
      statements: this.desire_statements,
      benefits: this.benefits,
      emotion_tone: this.emotion_tone
    },
    action: {
      prompts: this.action_prompts,
      call_to_action: this.call_to_action
    }
  };
  
  return stageContent[stage] || {};
};

// Instance method to get objection responses
aidaProductSchema.methods.getObjectionResponse = function(objectionType) {
  const responses = this.objection_responses[objectionType];
  if (responses && responses.length > 0) {
    return responses[Math.floor(Math.random() * responses.length)];
  }
  return null;
};

module.exports = mongoose.model('AidaProduct', aidaProductSchema);

