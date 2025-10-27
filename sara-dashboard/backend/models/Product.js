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
  price: {
    type: String
  },
  key_features: [String],
  selling_points: [String],
  common_objections: [{ 
    objection: String, 
    response: String 
  }],
  faqs: [{
    question: String,
    answer: String
  }],
  target_audience: String,
  
  // Custom fields - flexible key-value pairs
  custom_fields: [{
    field_name: { type: String, required: true },
    field_value: { type: String, required: true }
  }],
  
  // Active status - ONLY ONE can be true at a time
  isActive: { 
    type: Boolean, 
    default: false,
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

// Pre-save middleware to ensure only one product is active
productSchema.pre('save', async function(next) {
  if (this.isActive) {
    await this.constructor.updateMany(
      { _id: { $ne: this._id } },
      { isActive: false }
    );
  }
  next();
});

// Pre-save middleware to update timestamp
productSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

// Static method to get active product
productSchema.statics.getActive = async function() {
  return await this.findOne({ isActive: true });
};

// Static method to get all products
productSchema.statics.getAll = async function() {
  return await this.find({}).sort({ createdAt: -1 });
};

module.exports = mongoose.model('Product', productSchema);
