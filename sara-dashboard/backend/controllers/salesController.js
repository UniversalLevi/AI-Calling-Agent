/**
 * Sales Controller
 * Handles CRUD operations for sales-related data
 */

const Product = require('../models/Product');
const SalesScript = require('../models/SalesScript');
const ObjectionHandler = require('../models/ObjectionHandler');
const SalesTechnique = require('../models/SalesTechnique');
const SalesAnalytics = require('../models/SalesAnalytics');

// Product Management
const getProducts = async (req, res) => {
  try {
    const products = await Product.getAll();
    res.json({
      success: true,
      data: products,
      count: products.length
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
};

// Get active product
const getActiveProduct = async (req, res) => {
  try {
    const product = await Product.findOne({ isActive: true });
    res.json({ success: true, data: product });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// Activate a product (deactivates others)
const activateProduct = async (req, res) => {
  try {
    const { id } = req.params;
    
    // Deactivate all products
    await Product.updateMany({}, { isActive: false });
    
    // Activate the selected product
    const product = await Product.findByIdAndUpdate(
      id,
      { isActive: true, updatedAt: Date.now() },
      { new: true }
    );
    
    res.json({ success: true, data: product });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// Create product with custom fields
const createProduct = async (req, res) => {
  try {
    const productData = req.body;
    const product = new Product(productData);
    await product.save();
    res.status(201).json({ success: true, data: product });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// Update product with custom fields
const updateProduct = async (req, res) => {
  try {
    const { id } = req.params;
    const product = await Product.findByIdAndUpdate(
      id,
      { ...req.body, updatedAt: Date.now() },
      { new: true }
    );
    res.json({ success: true, data: product });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// Set Active Product (only one active at a time)
const setActiveProduct = async (req, res) => {
  try {
    const { id } = req.params;
    const product = await Product.findById(id);
    if (!product) {
      return res.status(404).json({ success: false, message: 'Product not found' });
    }

    // Deactivate all products first
    await Product.updateMany({ isActive: true }, { $set: { isActive: false } });
    // Activate selected product
    product.isActive = true;
    await product.save();

    res.json({ success: true, message: 'Active product set successfully', data: product });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Error setting active product', error: error.message });
  }
};

const getProduct = async (req, res) => {
  try {
    const product = await Product.findById(req.params.id);
    if (!product) {
      return res.status(404).json({
        success: false,
        message: 'Product not found'
      });
    }

    res.json({
      success: true,
      data: product
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching product',
      error: error.message
    });
  }
};

const deleteProduct = async (req, res) => {
  try {
    const product = await Product.findByIdAndDelete(req.params.id);
    if (!product) {
      return res.status(404).json({
        success: false,
        message: 'Product not found'
      });
    }

    res.json({
      success: true,
      message: 'Product deleted successfully'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error deleting product',
      error: error.message
    });
  }
};

// Sales Script Management
const getSalesScripts = async (req, res) => {
  try {
    const { productId, scriptType, technique, language } = req.query;
    let query = { isActive: true };

    if (productId) query.productId = productId;
    if (scriptType) query.scriptType = scriptType;
    if (technique) query.technique = technique;
    if (language) query.language = language;

    const scripts = await SalesScript.find(query).sort({ priority: -1, successRate: -1 });
    res.json({
      success: true,
      data: scripts,
      count: scripts.length
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching sales scripts',
      error: error.message
    });
  }
};

const createSalesScript = async (req, res) => {
  try {
    const script = new SalesScript(req.body);
    await script.save();

    res.status(201).json({
      success: true,
      data: script,
      message: 'Sales script created successfully'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      message: 'Error creating sales script',
      error: error.message
    });
  }
};

// Update script usage statistics
const updateScriptUsage = async (req, res) => {
  try {
    const { id } = req.params;
    const { success } = req.body;
    
    const script = await SalesScript.findById(id);
    if (!script) {
      return res.status(404).json({
        success: false,
        message: 'Script not found'
      });
    }
    
    // Update usage count and success rate
    script.usageCount += 1;
    const currentRate = script.successRate;
    const newRate = ((currentRate * (script.usageCount - 1)) + (success ? 100 : 0)) / script.usageCount;
    script.successRate = Math.round(newRate);
    
    await script.save();
    
    res.json({
      success: true,
      message: 'Script usage updated successfully',
      data: {
        usageCount: script.usageCount,
        successRate: script.successRate
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error updating script usage',
      error: error.message
    });
  }
};

const updateSalesScript = async (req, res) => {
  try {
    const script = await SalesScript.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true, runValidators: true }
    );

    if (!script) {
      return res.status(404).json({
        success: false,
        message: 'Sales script not found'
      });
    }

    res.json({
      success: true,
      data: script,
      message: 'Sales script updated successfully'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      message: 'Error updating sales script',
      error: error.message
    });
  }
};

// Objection Handler Management
const getObjectionHandlers = async (req, res) => {
  try {
    const { objectionType, technique, language } = req.query;
    let query = { isActive: true };

    if (objectionType) query.objectionType = objectionType;
    if (technique) query.technique = technique;
    if (language) query.language = language;

    const handlers = await ObjectionHandler.find(query).sort({ priority: -1, successRate: -1 });
    res.json({
      success: true,
      data: handlers,
      count: handlers.length
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching objection handlers',
      error: error.message
    });
  }
};

const detectObjection = async (req, res) => {
  try {
    const { userInput, language = 'en' } = req.body;
    const objectionTypes = await ObjectionHandler.detectObjectionType(userInput, language);
    
    res.json({
      success: true,
      data: {
        objectionTypes,
        userInput,
        language
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error detecting objection',
      error: error.message
    });
  }
};

const getObjectionResponse = async (req, res) => {
  try {
    const { objectionType, language = 'en' } = req.params;
    const handler = await ObjectionHandler.getBestHandler(objectionType, language);
    
    if (!handler) {
      return res.status(404).json({
        success: false,
        message: 'No objection handler found'
      });
    }

    res.json({
      success: true,
      data: handler
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching objection response',
      error: error.message
    });
  }
};

// Sales Technique Management
const getSalesTechniques = async (req, res) => {
  try {
    const { type, stage, language } = req.query;
    let query = { isActive: true };

    if (type) query.type = type;
    if (stage) query.stage = stage;
    if (language) query.language = language;

    const techniques = await SalesTechnique.find(query).sort({ priority: -1, successRate: -1 });
    res.json({
      success: true,
      data: techniques,
      count: techniques.length
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching sales techniques',
      error: error.message
    });
  }
};

// Active Campaign Configuration
const getActiveCampaign = async (req, res) => {
  try {
    const { productId } = req.params;
    
    const product = await Product.findById(productId);
    if (!product) {
      return res.status(404).json({
        success: false,
        message: 'Product not found'
      });
    }

    const scripts = await SalesScript.find({ productId, isActive: true }).sort({ priority: -1 });
    const objectionHandlers = await ObjectionHandler.find({ isActive: true }).sort({ priority: -1 });
    const techniques = await SalesTechnique.find({ isActive: true }).sort({ priority: -1 });

    res.json({
      success: true,
      data: {
        product,
        scripts,
        objectionHandlers,
        techniques
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching active campaign',
      error: error.message
    });
  }
};

module.exports = {
  // Product Management
  getProducts,
  getProduct,
  createProduct,
  updateProduct,
  deleteProduct,
  setActiveProduct,
  getActiveProduct,
  activateProduct,
  
  // Sales Script Management
  getSalesScripts,
  createSalesScript,
  updateSalesScript,
  updateScriptUsage,
  
  // Objection Handler Management
  getObjectionHandlers,
  detectObjection,
  getObjectionResponse,
  
  // Sales Technique Management
  getSalesTechniques,
  
  // Campaign Management
  getActiveCampaign
};
