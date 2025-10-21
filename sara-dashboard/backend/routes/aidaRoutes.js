/**
 * AIDA Routes
 * API endpoints for AIDA product management and analytics
 */

const express = require('express');
const router = express.Router();
const {
  getAidaProducts,
  getAidaProduct,
  createAidaProduct,
  updateAidaProduct,
  deleteAidaProduct,
  getActiveAidaProduct,
  setActiveAidaProduct,
  getAidaAnalytics,
  getProductPerformance,
  testAidaFlow,
  bulkUpdateAidaProducts
} = require('../controllers/aidaController');

const { authMiddleware, authorize, requirePermission } = require('../middleware/authMiddleware');

// Apply authentication to all routes
router.use(authMiddleware);

// Product Management Routes
router.get('/', requirePermission('canViewAnalytics'), getAidaProducts);
router.get('/analytics', requirePermission('canViewAnalytics'), getAidaAnalytics);
router.get('/active', getActiveAidaProduct);
router.get('/:id', requirePermission('canViewAnalytics'), getAidaProduct);
router.get('/:id/performance', requirePermission('canViewAnalytics'), getProductPerformance);

// Product CRUD Routes (Admin only)
router.post('/', authorize('admin'), createAidaProduct);
router.put('/:id', authorize('admin'), updateAidaProduct);
router.delete('/:id', authorize('admin'), deleteAidaProduct);

// Active Product Management (Admin only)
router.post('/set-active', authorize('admin'), setActiveAidaProduct);

// Testing Routes (Admin only)
router.post('/test-flow', authorize('admin'), testAidaFlow);

// Bulk Operations (Admin only)
router.post('/bulk-update', authorize('admin'), bulkUpdateAidaProducts);

module.exports = router;

