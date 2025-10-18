/**
 * Analytics Controller
 * Handles sales analytics and performance metrics
 */

const SalesAnalytics = require('../models/SalesAnalytics');
const LeadQualification = require('../models/LeadQualification');
const SalesScript = require('../models/SalesScript');
const ObjectionHandler = require('../models/ObjectionHandler');
const SalesTechnique = require('../models/SalesTechnique');

// Conversion Funnel Analysis
const getConversionFunnel = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    const funnelData = await SalesAnalytics.getConversionFunnel(startDate, endDate);
    
    res.json({
      success: true,
      data: funnelData
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching conversion funnel',
      error: error.message
    });
  }
};

// Objection Analysis
const getObjectionAnalysis = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    const objectionData = await SalesAnalytics.getObjectionAnalysis(startDate, endDate);
    
    res.json({
      success: true,
      data: objectionData
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching objection analysis',
      error: error.message
    });
  }
};

// Technique Performance Analysis
const getTechniquePerformance = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    const techniqueData = await SalesAnalytics.getTechniquePerformance(startDate, endDate);
    
    res.json({
      success: true,
      data: techniqueData
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching technique performance',
      error: error.message
    });
  }
};

// Sentiment Trends Analysis
const getSentimentTrends = async (req, res) => {
  try {
    const { startDate, endDate, callId } = req.query;
    let query = {};
    
    if (startDate && endDate) {
      query.createdAt = {
        $gte: new Date(startDate),
        $lte: new Date(endDate)
      };
    }
    
    if (callId) {
      query.callId = callId;
    }

    const sentimentData = await SalesAnalytics.aggregate([
      { $match: query },
      { $unwind: '$sentimentHistory' },
      {
        $group: {
          _id: {
            date: { $dateToString: { format: '%Y-%m-%d', date: '$sentimentHistory.timestamp' } },
            hour: { $hour: '$sentimentHistory.timestamp' }
          },
          averageSentiment: { $avg: '$sentimentHistory.score' },
          count: { $sum: 1 }
        }
      },
      {
        $sort: { '_id.date': 1, '_id.hour': 1 }
      }
    ]);

    res.json({
      success: true,
      data: sentimentData
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching sentiment trends',
      error: error.message
    });
  }
};

// Talk-Listen Ratio Analysis
const getTalkListenRatio = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    let matchStage = {};
    
    if (startDate && endDate) {
      matchStage.createdAt = {
        $gte: new Date(startDate),
        $lte: new Date(endDate)
      };
    }

    const ratioData = await SalesAnalytics.aggregate([
      { $match: matchStage },
      {
        $group: {
          _id: null,
          averageRatio: { $avg: '$talkListenRatio.ratio' },
          targetRatio: { $first: '$talkListenRatio.targetRatio' },
          totalCalls: { $sum: 1 },
          optimalCalls: {
            $sum: {
              $cond: [
                {
                  $and: [
                    { $gte: ['$talkListenRatio.ratio', 0.3] },
                    { $lte: ['$talkListenRatio.ratio', 0.5] }
                  ]
                },
                1,
                0
              ]
            }
          }
        }
      }
    ]);

    res.json({
      success: true,
      data: ratioData[0] || {
        averageRatio: 0,
        targetRatio: 0.4,
        totalCalls: 0,
        optimalCalls: 0
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching talk-listen ratio',
      error: error.message
    });
  }
};

// Keyword Success Analysis
const getKeywordSuccess = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    let matchStage = {};
    
    if (startDate && endDate) {
      matchStage.createdAt = {
        $gte: new Date(startDate),
        $lte: new Date(endDate)
      };
    }

    const keywordData = await SalesAnalytics.aggregate([
      { $match: matchStage },
      { $unwind: '$keyPhrases' },
      {
        $group: {
          _id: {
            phrase: '$keyPhrases.phrase',
            category: '$keyPhrases.category'
          },
          count: { $sum: 1 },
          conversionRate: {
            $avg: {
              $cond: [
                { $eq: ['$outcomeType', 'converted'] },
                1,
                0
              ]
            }
          },
          averageSentiment: { $avg: '$sentimentScore' }
        }
      },
      {
        $addFields: {
          conversionRate: { $multiply: ['$conversionRate', 100] }
        }
      },
      {
        $sort: { conversionRate: -1, count: -1 }
      },
      { $limit: 50 }
    ]);

    res.json({
      success: true,
      data: keywordData
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching keyword success data',
      error: error.message
    });
  }
};

// Call Quality Analysis
const getCallQuality = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    let matchStage = {};
    
    if (startDate && endDate) {
      matchStage.createdAt = {
        $gte: new Date(startDate),
        $lte: new Date(endDate)
      };
    }

    const qualityData = await SalesAnalytics.aggregate([
      { $match: matchStage },
      {
        $group: {
          _id: null,
          averageQuality: { $avg: '$callQuality.score' },
          totalCalls: { $sum: 1 },
          highQualityCalls: {
            $sum: { $cond: [{ $gte: ['$callQuality.score', 80] }, 1, 0] }
          },
          mediumQualityCalls: {
            $sum: {
              $cond: [
                {
                  $and: [
                    { $gte: ['$callQuality.score', 60] },
                    { $lt: ['$callQuality.score', 80] }
                  ]
                },
                1,
                0
              ]
            }
          },
          lowQualityCalls: {
            $sum: { $cond: [{ $lt: ['$callQuality.score', 60] }, 1, 0] }
          }
        }
      }
    ]);

    res.json({
      success: true,
      data: qualityData[0] || {
        averageQuality: 0,
        totalCalls: 0,
        highQualityCalls: 0,
        mediumQualityCalls: 0,
        lowQualityCalls: 0
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching call quality data',
      error: error.message
    });
  }
};

// Lead Qualification Statistics
const getQualificationStats = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    const stats = await LeadQualification.getQualificationStats(startDate, endDate);
    
    res.json({
      success: true,
      data: stats
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching qualification stats',
      error: error.message
    });
  }
};

// Real-time Call Monitoring
const getRealTimeMonitoring = async (req, res) => {
  try {
    const activeCalls = await SalesAnalytics.find({
      conversionStage: { $in: ['greeting', 'qualification', 'presentation', 'objection', 'closing'] }
    }).sort({ createdAt: -1 }).limit(10);

    res.json({
      success: true,
      data: activeCalls
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching real-time monitoring data',
      error: error.message
    });
  }
};

// Dashboard Summary
const getDashboardSummary = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    
    // Get various analytics in parallel
    const [
      funnelData,
      objectionData,
      techniqueData,
      qualificationStats,
      callQuality,
      talkListenRatio
    ] = await Promise.all([
      SalesAnalytics.getConversionFunnel(startDate, endDate),
      SalesAnalytics.getObjectionAnalysis(startDate, endDate),
      SalesAnalytics.getTechniquePerformance(startDate, endDate),
      LeadQualification.getQualificationStats(startDate, endDate),
      SalesAnalytics.aggregate([
        { $match: startDate && endDate ? {
          createdAt: { $gte: new Date(startDate), $lte: new Date(endDate) }
        } : {} },
        { $group: { _id: null, averageQuality: { $avg: '$callQuality.score' } } }
      ]),
      SalesAnalytics.aggregate([
        { $match: startDate && endDate ? {
          createdAt: { $gte: new Date(startDate), $lte: new Date(endDate) }
        } : {} },
        { $group: { _id: null, averageRatio: { $avg: '$talkListenRatio.ratio' } } }
      ])
    ]);

    res.json({
      success: true,
      data: {
        conversionFunnel: funnelData,
        objectionAnalysis: objectionData,
        techniquePerformance: techniqueData,
        qualificationStats,
        callQuality: callQuality[0]?.averageQuality || 0,
        talkListenRatio: talkListenRatio[0]?.averageRatio || 0
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Error fetching dashboard summary',
      error: error.message
    });
  }
};

module.exports = {
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
};
