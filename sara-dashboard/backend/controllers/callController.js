/**
 * Call Controller
 * Handles all call-related API endpoints
 */

const CallLog = require('../models/CallLog');
const { asyncHandler, AppError } = require('../middleware/errorHandler');

// @desc    Get all call logs
// @route   GET /api/calls
// @access  Private
const getCallLogs = asyncHandler(async (req, res) => {
  const {
    page = 1,
    limit = 10,
    type,
    status,
    caller,
    receiver,
    startDate,
    endDate,
    sortBy = 'createdAt',
    sortOrder = 'desc'
  } = req.query;

  // Build filter object
  const filter = {};
  
  if (type) filter.type = type;
  if (status) filter.status = status;
  if (caller) filter.caller = { $regex: caller, $options: 'i' };
  if (receiver) filter.receiver = { $regex: receiver, $options: 'i' };
  
  if (startDate || endDate) {
    filter.createdAt = {};
    if (startDate) filter.createdAt.$gte = new Date(startDate);
    if (endDate) filter.createdAt.$lte = new Date(endDate);
  }

  // Calculate pagination
  const pageNum = parseInt(page);
  const limitNum = parseInt(limit);
  const skip = (pageNum - 1) * limitNum;

  // Build sort object
  const sort = {};
  sort[sortBy] = sortOrder === 'desc' ? -1 : 1;

  // Execute query
  const calls = await CallLog.find(filter)
    .sort(sort)
    .skip(skip)
    .limit(limitNum);

  const total = await CallLog.countDocuments(filter);

  res.json({
    success: true,
    data: calls,
    pagination: {
      current: pageNum,
      pages: Math.ceil(total / limitNum),
      total,
      limit: limitNum
    }
  });
});

// @desc    Get call statistics
// @route   GET /api/calls/stats
// @access  Private
const getCallStats = asyncHandler(async (req, res) => {
  const { startDate, endDate } = req.query;
  
  const stats = await CallLog.getCallStats(startDate, endDate);
  const dailyTrends = await CallLog.getDailyTrends(7);
  
  // Calculate success rate
  const successRate = stats.totalCalls > 0 
    ? ((stats.successfulCalls / stats.totalCalls) * 100).toFixed(2)
    : 0;

  res.json({
    success: true,
    data: {
      ...stats,
      successRate: parseFloat(successRate),
      dailyTrends
    }
  });
});

// @desc    Get single call log
// @route   GET /api/calls/:id
// @access  Private
const getCallLog = asyncHandler(async (req, res) => {
  const call = await CallLog.findById(req.params.id)
    .populate('lastModifiedBy', 'username firstName lastName');

  if (!call) {
    throw new AppError('Call log not found', 404);
  }

  res.json({
    success: true,
    data: call
  });
});

// @desc    Create new call log
// @route   POST /api/calls
// @access  Private
const createCallLog = asyncHandler(async (req, res) => {
  const call = await CallLog.create(req.body);

  res.status(201).json({
    success: true,
    data: call
  });
});

// @desc    Update call log
// @route   PUT /api/calls/:id
// @access  Private
const updateCallLog = asyncHandler(async (req, res) => {
  let call;
  
  // Calculate duration if endTime is provided
  if (req.body.endTime) {
    // Find the call first to get startTime
    let existingCall;
    if (req.params.id.match(/^[0-9a-fA-F]{24}$/)) {
      existingCall = await CallLog.findById(req.params.id);
    } else {
      existingCall = await CallLog.findOne({ callId: req.params.id });
    }
    
    if (existingCall && existingCall.startTime) {
      const startTime = new Date(existingCall.startTime);
      const endTime = new Date(req.body.endTime);
      req.body.duration = Math.floor((endTime - startTime) / 1000); // duration in seconds
    }
  }
  
  // Try to find by MongoDB _id first, then by callId
  if (req.params.id.match(/^[0-9a-fA-F]{24}$/)) {
    call = await CallLog.findByIdAndUpdate(
      req.params.id,
      req.body,
      {
        new: true,
        runValidators: true
      }
    );
  } else {
    call = await CallLog.findOneAndUpdate(
      { callId: req.params.id },
      req.body,
      {
        new: true,
        runValidators: true
      }
    );
  }

  if (!call) {
    throw new AppError('Call log not found', 404);
  }

  // Emit socket event for real-time update
  if (req.app.get('io')) {
    req.app.get('io').emit('callUpdated', {
      callId: call.callId,
      data: call,
      timestamp: new Date()
    });
  }

  res.json({
    success: true,
    data: call
  });
});

// @desc    Update call transcript
// @route   PATCH /api/calls/:id/transcript
// @access  Public (for bot integration)
const updateCallTranscript = asyncHandler(async (req, res) => {
  const { transcript } = req.body;
  
  let call;
  
  // Try to find by MongoDB _id first, then by callId
  if (req.params.id.match(/^[0-9a-fA-F]{24}$/)) {
    call = await CallLog.findById(req.params.id);
  } else {
    call = await CallLog.findOne({ callId: req.params.id });
  }

  if (!call) {
    throw new AppError('Call log not found', 404);
  }

  // Append to existing transcript
  call.transcript += transcript;
  await call.save();

  // Emit socket event for real-time update
  if (req.app.get('io')) {
    req.app.get('io').emit('transcriptUpdated', {
      callId: call.callId,
      transcript: call.transcript,
      timestamp: new Date()
    });
  }

  res.json({
    success: true,
    data: { transcript: call.transcript }
  });
});

// @desc    Delete call log
// @route   DELETE /api/calls/:id
// @access  Private
const deleteCallLog = asyncHandler(async (req, res) => {
  const call = await CallLog.findByIdAndDelete(req.params.id);

  if (!call) {
    throw new AppError('Call log not found', 404);
  }

  res.json({
    success: true,
    message: 'Call log deleted successfully'
  });
});

// @desc    Get active calls
// @route   GET /api/calls/active
// @access  Private
const getActiveCalls = asyncHandler(async (req, res) => {
  // First, cleanup any stuck calls (older than 1 hour)
  const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
  await CallLog.updateMany(
    { 
      status: 'in-progress',
      startTime: { $lt: oneHourAgo }
    },
    { 
      status: 'failed',
      endTime: new Date(),
      metadata: { 
        cleanup_reason: 'stuck_call_timeout',
        original_status: 'in-progress'
      }
    }
  );

  const activeCalls = await CallLog.find({ 
    status: 'in-progress' 
  }).sort({ startTime: -1 });

  res.json({
    success: true,
    data: activeCalls
  });
});

// @desc    Terminate call
// @route   POST /api/calls/:id/terminate
// @access  Private
const terminateCall = asyncHandler(async (req, res) => {
  const call = await CallLog.findById(req.params.id);

  if (!call) {
    throw new AppError('Call log not found', 404);
  }

  if (call.status !== 'in-progress') {
    throw new AppError('Call is not active', 400);
  }

  // Update call status
  call.status = 'failed';
  call.endTime = new Date();
  await call.save();

  // Emit socket event for real-time update
  req.app.get('io').emit('callTerminated', {
    callId: call.callId,
    status: 'terminated',
    timestamp: new Date()
  });

  res.json({
    success: true,
    message: 'Call terminated successfully',
    data: call
  });
});

// @desc    Get call analytics
// @route   GET /api/calls/analytics
// @access  Private
const getCallAnalytics = asyncHandler(async (req, res) => {
  const { period = '7d' } = req.query;
  
  let days;
  switch (period) {
    case '1d': days = 1; break;
    case '7d': days = 7; break;
    case '30d': days = 30; break;
    case '90d': days = 90; break;
    default: days = 7;
  }

  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  // Get various analytics
  const [
    totalStats,
    dailyTrends,
    hourlyDistribution,
    languageDistribution,
    statusDistribution
  ] = await Promise.all([
    CallLog.getCallStats(startDate, new Date()),
    CallLog.getDailyTrends(days),
    getHourlyDistribution(startDate),
    getLanguageDistribution(startDate),
    getStatusDistribution(startDate)
  ]);

  res.json({
    success: true,
    data: {
      period,
      totalStats,
      dailyTrends,
      hourlyDistribution,
      languageDistribution,
      statusDistribution
    }
  });
});

// Helper function to get hourly distribution
const getHourlyDistribution = async (startDate) => {
  return await CallLog.aggregate([
    {
      $match: {
        createdAt: { $gte: startDate }
      }
    },
    {
      $group: {
        _id: { $hour: '$createdAt' },
        count: { $sum: 1 }
      }
    },
    {
      $sort: { '_id': 1 }
    }
  ]);
};

// Helper function to get language distribution
const getLanguageDistribution = async (startDate) => {
  return await CallLog.aggregate([
    {
      $match: {
        createdAt: { $gte: startDate }
      }
    },
    {
      $group: {
        _id: '$language',
        count: { $sum: 1 }
      }
    }
  ]);
};

// Helper function to get status distribution
const getStatusDistribution = async (startDate) => {
  return await CallLog.aggregate([
    {
      $match: {
        createdAt: { $gte: startDate }
      }
    },
    {
      $group: {
        _id: '$status',
        count: { $sum: 1 }
      }
    }
  ]);
};

// @desc    Cleanup stuck calls
// @route   POST /api/calls/cleanup
// @access  Private
const cleanupStuckCalls = asyncHandler(async (req, res) => {
  const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
  
  const result = await CallLog.updateMany(
    { 
      status: 'in-progress',
      startTime: { $lt: oneHourAgo }
    },
    { 
      status: 'failed',
      endTime: new Date(),
      metadata: { 
        cleanup_reason: 'manual_cleanup',
        original_status: 'in-progress'
      }
    }
  );

  res.json({
    success: true,
    message: 'Cleaned up ' + result.modifiedCount + ' stuck calls',
    data: {
      modifiedCount: result.modifiedCount
    }
  });
});

module.exports = {
  getCallLogs,
  getCallStats,
  getCallLog,
  createCallLog,
  updateCallLog,
  updateCallTranscript,
  deleteCallLog,
  getActiveCalls,
  terminateCall,
  getCallAnalytics,
  cleanupStuckCalls
};
