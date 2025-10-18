/**
 * Product Model
 * Database schema for storing product catalog with sales details
 */

const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true,
    index: true
  },
  description: {
    type: String,
    required: true,
    trim: true
  },
  category: {
    type: String,
    required: true,
    enum: ['hotel', 'insurance', 'saas', 'real_estate', 'ecommerce', 'services', 'other'],
    index: true
  },
  price: {
    type: Number,
    required: true,
    min: 0
  },
  currency: {
    type: String,
    default: 'USD',
    enum: ['USD', 'INR', 'EUR', 'GBP']
  },
  features: [{
    name: String,
    description: String,
    benefit: String
  }],
  faqs: [{
    question: String,
    answer: String,
    language: {
      type: String,
      enum: ['en', 'hi', 'mixed'],
      default: 'en'
    }
  }],
  targetAudience: {
    demographics: {
      ageRange: String,
      incomeLevel: String,
      location: String
    },
    painPoints: [String],
    buyingMotivations: [String]
  },
  competitorComparison: [{
    competitorName: String,
    ourAdvantage: String,
    theirWeakness: String
  }],
  salesPitch: {
    opening: String,
    valueProposition: String,
    urgencyFactors: [String],
    closingPhrases: [String]
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
  tags: [String],
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
productSchema.index({ name: 1 }, { unique: true });
productSchema.index({ category: 1, isActive: 1 });
productSchema.index({ priority: -1, isActive: 1 });

// Pre-save middleware to update timestamp
productSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

// Static method to get active products by category
productSchema.statics.getActiveByCategory = async function(category) {
  return await this.find({ category, isActive: true }).sort({ priority: -1 });
};

// Static method to get all active products
productSchema.statics.getAllActive = async function() {
  return await this.find({ isActive: true }).sort({ priority: -1, name: 1 });
};

// Static method to search products
productSchema.statics.searchProducts = async function(query, category = null) {
  const searchCriteria = {
    isActive: true,
    $or: [
      { name: { $regex: query, $options: 'i' } },
      { description: { $regex: query, $options: 'i' } },
      { tags: { $in: [new RegExp(query, 'i')] } }
    ]
  };
  
  if (category) {
    searchCriteria.category = category;
  }
  
  return await this.find(searchCriteria).sort({ priority: -1 });
};

// Virtual for formatted price
productSchema.virtual('formattedPrice').get(function() {
  return `${this.currency} ${this.price.toLocaleString()}`;
});

// Virtual for product summary
productSchema.virtual('summary').get(function() {
  return {
    id: this._id,
    name: this.name,
    category: this.category,
    price: this.formattedPrice,
    isActive: this.isActive,
    priority: this.priority
  };
});

module.exports = mongoose.model('Product', productSchema);
