/**
 * AIDA Controller
 * Handles CRUD operations for AIDA products and analytics
 */

const AidaProduct = require('../models/AidaProduct');
const { asyncHandler, AppError } = require('../middleware/errorHandler');

// Product Management
const getAidaProducts = async (req, res) => {
  try {
    const { category, product_type, isActive, search, page = 1, limit = 10 } = req.query;
    
    // Build filter object
    const filter = {};
    if (category) filter.category = category;
    if (product_type) filter.product_type = product_type;
    if (isActive !== undefined) filter.isActive = isActive === 'true';
    if (search) {
      filter.$or = [
        { product_name: { $regex: search, $options: 'i' } },
        { brand_name: { $regex: search, $options: 'i' } },
        { offer_tagline: { $regex: search, $options: 'i' } }
      ];
    }
    
    // Calculate pagination
    const pageNum = parseInt(page);
    const limitNum = parseInt(limit);
    const skip = (pageNum - 1) * limitNum;
    
    // Execute query
    const products = await AidaProduct.find(filter)
      .populate('createdBy', 'username email')
      .populate('lastModifiedBy', 'username email')
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limitNum);
    
    const total = await AidaProduct.countDocuments(filter);
    
    res.json({
      success: true,
      data: products,
      pagination: {
        page: pageNum,
        limit: limitNum,
        total,
        pages: Math.ceil(total / limitNum)
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching AIDA products',
      error: error.message
    });
  }
};

const getAidaProduct = async (req, res) => {
  try {
    const product = await AidaProduct.findById(req.params.id)
      .populate('createdBy', 'username email')
      .populate('lastModifiedBy', 'username email');
    
    if (!product) {
      return res.status(404).json({
        success: false,
        message: 'AIDA product not found'
      });
    }
    
    res.json({
      success: true,
      data: product
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching AIDA product',
      error: error.message
    });
  }
};

const createAidaProduct = async (req, res) => {
  try {
    const productData = {
      ...req.body,
      createdBy: req.user._id,
      lastModifiedBy: req.user._id
    };
    
    const product = await AidaProduct.create(productData);
    
    res.status(201).json({
      success: true,
      data: product,
      message: 'AIDA product created successfully'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      message: 'Error creating AIDA product',
      error: error.message
    });
  }
};

const updateAidaProduct = async (req, res) => {
  try {
    const productData = {
      ...req.body,
      lastModifiedBy: req.user._id
    };
    
    const product = await AidaProduct.findByIdAndUpdate(
      req.params.id,
      productData,
      { new: true, runValidators: true }
    ).populate('createdBy', 'username email')
     .populate('lastModifiedBy', 'username email');
    
    if (!product) {
      return res.status(404).json({
        success: false,
        message: 'AIDA product not found'
      });
    }
    
    res.json({
      success: true,
      data: product,
      message: 'AIDA product updated successfully'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      message: 'Error updating AIDA product',
      error: error.message
    });
  }
};

const deleteAidaProduct = async (req, res) => {
  try {
    const product = await AidaProduct.findByIdAndDelete(req.params.id);
    
    if (!product) {
      return res.status(404).json({
        success: false,
        message: 'AIDA product not found'
      });
    }
    
    res.json({
      success: true,
      message: 'AIDA product deleted successfully'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error deleting AIDA product',
      error: error.message
    });
  }
};

// Active Product Management
const getActiveAidaProduct = async (req, res) => {
  try {
    const activeProduct = await AidaProduct.getActiveProduct();
    
    if (!activeProduct) {
      return res.status(404).json({
        success: false,
        message: 'No active AIDA product found'
      });
    }
    
    res.json({
      success: true,
      data: activeProduct
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching active AIDA product',
      error: error.message
    });
  }
};

const setActiveAidaProduct = async (req, res) => {
  try {
    const { productId } = req.body;
    
    if (!productId) {
      return res.status(400).json({
        success: false,
        message: 'Product ID is required'
      });
    }
    
    const activeProduct = await AidaProduct.setActiveProduct(productId);
    
    res.json({
      success: true,
      data: activeProduct,
      message: 'Active AIDA product updated successfully'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      message: 'Error setting active AIDA product',
      error: error.message
    });
  }
};

// Analytics and Performance
const getAidaAnalytics = async (req, res) => {
  try {
    const { productId, startDate, endDate } = req.query;
    
    let filter = {};
    if (productId) {
      filter._id = productId;
    }
    
    const products = await AidaProduct.find(filter);
    
    const analytics = {
      totalProducts: products.length,
      activeProducts: products.filter(p => p.isActive).length,
      totalCalls: products.reduce((sum, p) => sum + p.analytics.total_calls, 0),
      totalConversions: products.reduce((sum, p) => sum + p.analytics.conversions, 0),
      avgConversionRate: 0,
      avgCallDuration: 0,
      categoryBreakdown: {},
      productTypeBreakdown: {},
      topPerformingProducts: []
    };
    
    // Calculate averages
    if (analytics.totalCalls > 0) {
      analytics.avgConversionRate = (analytics.totalConversions / analytics.totalCalls) * 100;
    }
    
    const totalDuration = products.reduce((sum, p) => sum + p.analytics.avg_call_duration, 0);
    if (products.length > 0) {
      analytics.avgCallDuration = totalDuration / products.length;
    }
    
    // Category breakdown
    products.forEach(product => {
      const category = product.category;
      if (!analytics.categoryBreakdown[category]) {
        analytics.categoryBreakdown[category] = {
          count: 0,
          totalCalls: 0,
          conversions: 0
        };
      }
      analytics.categoryBreakdown[category].count += 1;
      analytics.categoryBreakdown[category].totalCalls += product.analytics.total_calls;
      analytics.categoryBreakdown[category].conversions += product.analytics.conversions;
    });
    
    // Product type breakdown
    products.forEach(product => {
      const type = product.product_type;
      if (!analytics.productTypeBreakdown[type]) {
        analytics.productTypeBreakdown[type] = {
          count: 0,
          totalCalls: 0,
          conversions: 0
        };
      }
      analytics.productTypeBreakdown[type].count += 1;
      analytics.productTypeBreakdown[type].totalCalls += product.analytics.total_calls;
      analytics.productTypeBreakdown[type].conversions += product.analytics.conversions;
    });
    
    // Top performing products
    analytics.topPerformingProducts = products
      .filter(p => p.analytics.total_calls > 0)
      .sort((a, b) => b.analytics.conversion_rate - a.analytics.conversion_rate)
      .slice(0, 5)
      .map(p => ({
        id: p._id,
        name: p.product_name,
        brand: p.brand_name,
        conversionRate: p.analytics.conversion_rate,
        totalCalls: p.analytics.total_calls
      }));
    
    res.json({
      success: true,
      data: analytics
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching AIDA analytics',
      error: error.message
    });
  }
};

const getProductPerformance = async (req, res) => {
  try {
    const product = await AidaProduct.findById(req.params.id);
    
    if (!product) {
      return res.status(404).json({
        success: false,
        message: 'AIDA product not found'
      });
    }
    
    const performance = {
      product: {
        id: product._id,
        name: product.product_name,
        brand: product.brand_name,
        category: product.category,
        type: product.product_type
      },
      analytics: product.analytics,
      stagePerformance: {
        completionRates: product.analytics.stage_completion_rates,
        objectionFrequency: product.analytics.objection_frequency
      },
      calculatedMetrics: {
        conversionRate: product.calculatedConversionRate,
        avgCallDuration: product.analytics.avg_call_duration
      }
    };
    
    res.json({
      success: true,
      data: performance
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching product performance',
      error: error.message
    });
  }
};

// AIDA Framework Testing
const testAidaFlow = async (req, res) => {
  try {
    const { productId, testInput } = req.body;
    
    if (!productId || !testInput) {
      return res.status(400).json({
        success: false,
        message: 'Product ID and test input are required'
      });
    }
    
    const product = await AidaProduct.findById(productId);
    
    if (!product) {
      return res.status(404).json({
        success: false,
        message: 'AIDA product not found'
      });
    }
    
    // Simulate AIDA flow testing
    const testResult = {
      product: {
        id: product._id,
        name: product.product_name,
        brand: product.brand_name
      },
      testInput,
      suggestedResponses: {
        attention: product.getStageContent('attention'),
        interest: product.getStageContent('interest'),
        desire: product.getStageContent('desire'),
        action: product.getStageContent('action')
      },
      objectionHandling: {
        price: product.getObjectionResponse('price'),
        timing: product.getObjectionResponse('timing'),
        authority: product.getObjectionResponse('authority')
      }
    };
    
    res.json({
      success: true,
      data: testResult,
      message: 'AIDA flow test completed'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error testing AIDA flow',
      error: error.message
    });
  }
};

// Bulk Operations
const bulkUpdateAidaProducts = async (req, res) => {
  try {
    const { updates } = req.body;
    
    if (!Array.isArray(updates)) {
      return res.status(400).json({
        success: false,
        message: 'Updates must be an array'
      });
    }
    
    const results = [];
    
    for (const update of updates) {
      try {
        const product = await AidaProduct.findByIdAndUpdate(
          update.id,
          { ...update.data, lastModifiedBy: req.user._id },
          { new: true }
        );
        
        if (product) {
          results.push({ id: update.id, success: true, data: product });
        } else {
          results.push({ id: update.id, success: false, error: 'Product not found' });
        }
      } catch (error) {
        results.push({ id: update.id, success: false, error: error.message });
      }
    }
    
    res.json({
      success: true,
      data: results,
      message: 'Bulk update completed'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error in bulk update',
      error: error.message
    });
  }
};

module.exports = {
  // Product Management
  getAidaProducts,
  getAidaProduct,
  createAidaProduct,
  updateAidaProduct,
  deleteAidaProduct,
  
  // Active Product Management
  getActiveAidaProduct,
  setActiveAidaProduct,
  
  // Analytics and Performance
  getAidaAnalytics,
  getProductPerformance,
  
  // Testing
  testAidaFlow,
  
  // Bulk Operations
  bulkUpdateAidaProducts
};

