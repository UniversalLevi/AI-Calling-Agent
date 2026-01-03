/**
 * WhatsApp Controller
 * Handles WhatsApp message API operations
 */

const WhatsAppMessage = require('../models/WhatsAppMessage');
const CallLog = require('../models/CallLog');

/**
 * Create a new WhatsApp message record
 * @route POST /api/whatsapp/messages
 * @access Public (for bot integration)
 */
const createMessage = async (req, res) => {
  try {
    const {
      messageId,
      callId,
      phone,
      customerName,
      direction,
      type,
      content,
      template,
      paymentLinkId,
      paymentLinkUrl,
      status,
      error,
      metadata
    } = req.body;

    // Validate required fields
    if (!messageId || !phone || !content) {
      return res.status(400).json({
        success: false,
        message: 'Missing required fields: messageId, phone, content'
      });
    }

    // Check if message already exists
    const existingMessage = await WhatsAppMessage.findOne({ messageId });
    if (existingMessage) {
      return res.status(200).json({
        success: true,
        data: existingMessage,
        message: 'Message already exists'
      });
    }

    // Create new message
    const message = new WhatsAppMessage({
      messageId,
      callId,
      phone,
      customerName: customerName || 'Customer',
      direction: direction || 'outbound',
      type: type || 'text',
      content,
      template,
      paymentLinkId,
      paymentLinkUrl,
      status: status || 'sent',
      sentAt: status === 'sent' ? new Date() : null,
      error: error || null,
      metadata: metadata || {}
    });

    await message.save();

    // Update call log if callId provided
    if (callId) {
      await CallLog.findOneAndUpdate(
        { callId },
        { 
          $push: { whatsappMessages: message._id },
          $set: { 'metadata.hasWhatsAppMessages': true }
        }
      );
    }

    // Emit socket event for real-time updates
    const io = req.app.get('io');
    if (io) {
      io.emit('whatsapp:messageSent', message);
    }

    res.status(201).json({
      success: true,
      data: message
    });

  } catch (error) {
    console.error('Error creating WhatsApp message:', error);
    res.status(500).json({
      success: false,
      message: 'Error creating WhatsApp message',
      error: error.message
    });
  }
};

/**
 * Update message status
 * @route PATCH /api/whatsapp/messages/:id
 * @access Public (for webhook integration)
 */
const updateMessage = async (req, res) => {
  try {
    const { id } = req.params;
    const { status, error } = req.body;

    // Find by messageId or MongoDB _id
    let message = await WhatsAppMessage.findOne({ messageId: id });
    if (!message) {
      message = await WhatsAppMessage.findById(id);
    }

    if (!message) {
      return res.status(404).json({
        success: false,
        message: 'Message not found'
      });
    }

    // Update status
    if (status) {
      message.status = status;
    }

    // Update error if provided
    if (error) {
      message.error = {
        code: error.code,
        message: error.message,
        details: error.details,
        needsOptin: error.needsOptin || false
      };
    }

    await message.save();

    // Emit socket event
    const io = req.app.get('io');
    if (io) {
      io.emit('whatsapp:statusUpdate', message);
    }

    res.json({
      success: true,
      data: message
    });

  } catch (error) {
    console.error('Error updating WhatsApp message:', error);
    res.status(500).json({
      success: false,
      message: 'Error updating WhatsApp message',
      error: error.message
    });
  }
};

/**
 * Get all messages with pagination and filters
 * @route GET /api/whatsapp/messages
 * @access Private
 */
const getMessages = async (req, res) => {
  try {
    const {
      page = 1,
      limit = 20,
      status,
      type,
      direction,
      phone,
      callId,
      startDate,
      endDate,
      sortBy = 'createdAt',
      sortOrder = 'desc'
    } = req.query;

    // Build query
    const query = {};

    if (status) {
      query.status = status;
    }

    if (type) {
      query.type = type;
    }

    if (direction) {
      query.direction = direction;
    }

    if (phone) {
      query.phone = { $regex: phone, $options: 'i' };
    }

    if (callId) {
      query.callId = callId;
    }

    if (startDate || endDate) {
      query.createdAt = {};
      if (startDate) query.createdAt.$gte = new Date(startDate);
      if (endDate) query.createdAt.$lte = new Date(endDate);
    }

    // Execute query with pagination
    const skip = (parseInt(page) - 1) * parseInt(limit);
    const sort = { [sortBy]: sortOrder === 'desc' ? -1 : 1 };

    const [messages, total] = await Promise.all([
      WhatsAppMessage.find(query)
        .sort(sort)
        .skip(skip)
        .limit(parseInt(limit))
        .lean(),
      WhatsAppMessage.countDocuments(query)
    ]);

    res.json({
      success: true,
      data: messages,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
      }
    });

  } catch (error) {
    console.error('Error fetching WhatsApp messages:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching WhatsApp messages',
      error: error.message
    });
  }
};

/**
 * Get single message
 * @route GET /api/whatsapp/messages/:id
 * @access Private
 */
const getMessage = async (req, res) => {
  try {
    const { id } = req.params;

    let message = await WhatsAppMessage.findOne({ messageId: id });
    if (!message) {
      message = await WhatsAppMessage.findById(id);
    }

    if (!message) {
      return res.status(404).json({
        success: false,
        message: 'Message not found'
      });
    }

    res.json({
      success: true,
      data: message
    });

  } catch (error) {
    console.error('Error fetching WhatsApp message:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching WhatsApp message',
      error: error.message
    });
  }
};

/**
 * Get message statistics
 * @route GET /api/whatsapp/stats
 * @access Private
 */
const getMessageStats = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;

    const [stats, typeBreakdown, dailyTrends] = await Promise.all([
      WhatsAppMessage.getMessageStats(startDate, endDate),
      WhatsAppMessage.getTypeBreakdown(7),
      WhatsAppMessage.getDailyTrends(7)
    ]);

    res.json({
      success: true,
      data: {
        overview: stats,
        byType: typeBreakdown,
        dailyTrends
      }
    });

  } catch (error) {
    console.error('Error fetching WhatsApp stats:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching WhatsApp stats',
      error: error.message
    });
  }
};

/**
 * Get messages for a specific call
 * @route GET /api/whatsapp/call/:callId
 * @access Private
 */
const getMessagesByCall = async (req, res) => {
  try {
    const { callId } = req.params;

    const messages = await WhatsAppMessage.find({ callId })
      .sort({ createdAt: -1 })
      .lean();

    res.json({
      success: true,
      data: messages
    });

  } catch (error) {
    console.error('Error fetching messages for call:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching messages for call',
      error: error.message
    });
  }
};

/**
 * Delete message
 * @route DELETE /api/whatsapp/messages/:id
 * @access Private (Admin only)
 */
const deleteMessage = async (req, res) => {
  try {
    const { id } = req.params;

    const message = await WhatsAppMessage.findByIdAndDelete(id);

    if (!message) {
      return res.status(404).json({
        success: false,
        message: 'Message not found'
      });
    }

    // Remove reference from call log
    if (message.callId) {
      await CallLog.findOneAndUpdate(
        { callId: message.callId },
        { $pull: { whatsappMessages: message._id } }
      );
    }

    res.json({
      success: true,
      message: 'Message deleted successfully'
    });

  } catch (error) {
    console.error('Error deleting WhatsApp message:', error);
    res.status(500).json({
      success: false,
      message: 'Error deleting WhatsApp message',
      error: error.message
    });
  }
};

module.exports = {
  createMessage,
  updateMessage,
  getMessages,
  getMessage,
  getMessageStats,
  getMessagesByCall,
  deleteMessage
};

