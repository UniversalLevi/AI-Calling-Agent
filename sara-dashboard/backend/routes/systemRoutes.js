/**
 * System Routes
 * API routes for system configuration and management
 */

const express = require('express');
const router = express.Router();
const {
  getSystemConfigs,
  getSystemConfig,
  updateSystemConfig,
  bulkUpdateSystemConfigs,
  getSystemAnalytics,
  getSystemHealth,
  initializeDefaults,
  exportConfigs,
  importConfigs
} = require('../controllers/systemController');

const { authMiddleware, authorize, requirePermission } = require('../middleware/authMiddleware');

// Apply authentication to all routes
router.use(authMiddleware);

// @route   GET /api/system/config
// @desc    Get all system configurations
// @access  Private
router.get('/config', getSystemConfigs);

// @route   GET /api/system/config/:name
// @desc    Get system configuration by name
// @access  Private
router.get('/config/:name', getSystemConfig);

// @route   GET /api/system/analytics
// @desc    Get system analytics
// @access  Private
router.get('/analytics', requirePermission('canViewAnalytics'), getSystemAnalytics);

// @route   GET /api/system/health
// @desc    Get system health status
// @access  Private
router.get('/health', getSystemHealth);

// @route   GET /api/system/export
// @desc    Export system configurations
// @access  Private (Admin only)
router.get('/export', authorize('admin'), exportConfigs);

// Admin only routes
router.use(authorize('admin'));

// @route   PUT /api/system/config/:name
// @desc    Update system configuration
// @access  Private (Admin only)
router.put('/config/:name', updateSystemConfig);

// @route   PUT /api/system/config
// @desc    Bulk update system configurations
// @access  Private (Admin only)
router.put('/config', bulkUpdateSystemConfigs);

// @route   POST /api/system/init-defaults
// @desc    Initialize default configurations
// @access  Private (Admin only)
router.post('/init-defaults', initializeDefaults);

// @route   POST /api/system/import
// @desc    Import system configurations
// @access  Private (Admin only)
router.post('/import', importConfigs);

module.exports = router;
