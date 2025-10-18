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
  getSalesScripts,
  createSalesScript,
  updateSalesScript,
  getObjectionHandlers,
  detectObjection,
  getObjectionResponse,
  getSalesTechniques,
  getLeadQualification,
  updateLeadQualification,
  getActiveCampaign
} = require('../controllers/salesController');

// Product Management Routes
router.get('/products', getProducts);
router.get('/products/:id', getProduct);
router.post('/products', createProduct);
router.put('/products/:id', updateProduct);
router.delete('/products/:id', deleteProduct);

// Sales Script Management Routes
router.get('/scripts', getSalesScripts);
router.post('/scripts', createSalesScript);
router.put('/scripts/:id', updateSalesScript);

// Objection Handler Management Routes
router.get('/objections', getObjectionHandlers);
router.post('/objections/detect', detectObjection);
router.get('/objections/:objectionType/:language', getObjectionResponse);

// Sales Technique Management Routes
router.get('/techniques', getSalesTechniques);

// Lead Qualification Management Routes
router.get('/qualification/:callId', getLeadQualification);
router.put('/qualification/:callId', updateLeadQualification);

// Campaign Management Routes
router.get('/active-campaign/:productId', getActiveCampaign);

module.exports = router;
