/**
 * Analytics Routes
 * API endpoints for sales analytics and performance metrics
 */

const express = require('express');
const router = express.Router();
const {
  getConversionFunnel,
  getObjectionAnalysis,
  getTechniquePerformance,
  getSentimentTrends,
  getTalkListenRatio,
  getKeywordSuccess,
  getCallQuality,
  getQualificationStats,
  getRealTimeMonitoring,
  getDashboardSummary
} = require('../controllers/analyticsController');

// Analytics Routes
router.get('/conversion-funnel', getConversionFunnel);
router.get('/objection-analysis', getObjectionAnalysis);
router.get('/technique-performance', getTechniquePerformance);
router.get('/sentiment-trends', getSentimentTrends);
router.get('/talk-listen-ratio', getTalkListenRatio);
router.get('/keyword-success', getKeywordSuccess);
router.get('/call-quality', getCallQuality);
router.get('/qualification-stats', getQualificationStats);
router.get('/real-time-monitoring', getRealTimeMonitoring);
router.get('/dashboard-summary', getDashboardSummary);

module.exports = router;
