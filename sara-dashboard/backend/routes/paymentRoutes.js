/**
 * Payment Routes
 * API routes for payment link management
 */

const express = require('express');
const router = express.Router();
const {
  createPaymentLink,
  updatePaymentLink,
  getPaymentLinks,
  getPaymentLink,
  getPaymentStats,
  deletePaymentLink,
  getPaymentsByCall
} = require('../controllers/paymentController');

const { authMiddleware, authorize, requirePermission } = require('../middleware/authMiddleware');

// Public routes (for bot integration) - MUST come before auth middleware
router.post('/', createPaymentLink);
router.patch('/:id', updatePaymentLink);

// Apply authentication to dashboard routes
router.use(authMiddleware);

// Protected dashboard routes
router.get('/stats', getPaymentStats);
router.get('/call/:callId', getPaymentsByCall);
router.get('/', getPaymentLinks);
router.get('/:id', getPaymentLink);

// Admin only routes
router.delete('/:id', authorize('admin'), deletePaymentLink);

module.exports = router;

