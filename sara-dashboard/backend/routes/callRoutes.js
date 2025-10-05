/**
 * Call Routes
 * API routes for call management
 */

const express = require('express');
const router = express.Router();
const {
  getCallLogs,
  getCallStats,
  getCallLog,
  createCallLog,
  updateCallLog,
  updateCallTranscript,
  deleteCallLog,
  getActiveCalls,
  terminateCall,
  getCallAnalytics
} = require('../controllers/callController');

const { authMiddleware, authorize, requirePermission } = require('../middleware/authMiddleware');

// Public routes (for bot integration) - MUST come before auth middleware
router.post('/', createCallLog);
router.patch('/:id', updateCallLog);
router.patch('/:id/transcript', updateCallTranscript);

// Temporary public routes for testing (remove in production)
router.get('/stats', getCallStats);
router.get('/analytics', getCallAnalytics);
router.get('/active', getActiveCalls);
router.get('/', getCallLogs);

// Apply authentication to remaining routes
router.use(authMiddleware);

// @route   GET /api/calls/:id
// @desc    Get single call log
// @access  Private
router.get('/:id', requirePermission('canViewCalls'), getCallLog);

// Note: POST and PATCH routes are public (defined above for bot integration)

// @route   DELETE /api/calls/:id
// @desc    Delete call log
// @access  Private
router.delete('/:id', requirePermission('canManageCalls'), deleteCallLog);

// @route   POST /api/calls/:id/terminate
// @desc    Terminate active call
// @access  Private (Admin only)
router.post('/:id/terminate', authorize('admin'), terminateCall);

module.exports = router;
