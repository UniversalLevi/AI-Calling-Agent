/**
 * Sales Routes
 * API endpoints for sales management
 */

const express = require('express');
const router = express.Router();
const {
  getProducts,
  getProduct,
  createProduct,
  updateProduct,
  deleteProduct,
  setActiveProduct,
  getActiveProduct,
  activateProduct,
  getSalesScripts,
  createSalesScript,
  updateSalesScript,
  updateScriptUsage,
  getObjectionHandlers,
  detectObjection,
  getObjectionResponse,
  getSalesTechniques,
  getActiveCampaign
} = require('../controllers/salesController');

// Product Management Routes
router.get('/products/active', getActiveProduct);  // Specific route first
router.get('/products', getProducts);
router.get('/products/:id', getProduct);
router.post('/products', createProduct);
router.put('/products/:id', updateProduct);
router.delete('/products/:id', deleteProduct);
router.post('/products/:id/activate', activateProduct);

// Sales Script Management Routes
router.get('/scripts', getSalesScripts);
router.post('/scripts', createSalesScript);
router.put('/scripts/:id', updateSalesScript);
router.post('/scripts/:id/usage', updateScriptUsage);

// Objection Handler Management Routes
router.get('/objections', getObjectionHandlers);
router.post('/objections/detect', detectObjection);
router.get('/objections/:objectionType/:language', getObjectionResponse);

// Sales Technique Management Routes
router.get('/techniques', getSalesTechniques);

// Campaign Management Routes
router.get('/active-campaign/:productId', getActiveCampaign);

module.exports = router;
