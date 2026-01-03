/**
 * Payment Controller
 * Handles payment link API operations
 */

const PaymentLink = require('../models/PaymentLink');
const CallLog = require('../models/CallLog');

/**
 * Create a new payment link record
 * @route POST /api/payments
 * @access Public (for bot integration)
 */
const createPaymentLink = async (req, res) => {
  try {
    const {
      razorpayLinkId,
      callId,
      phone,
      customerName,
      amount,
      amountDisplay,
      currency,
      productName,
      productId,
      shortUrl,
      description,
      whatsappMessageId,
      expiresAt,
      metadata
    } = req.body;

    // Validate required fields
    if (!razorpayLinkId || !phone || !amount || !productName || !shortUrl) {
      return res.status(400).json({
        success: false,
        message: 'Missing required fields: razorpayLinkId, phone, amount, productName, shortUrl'
      });
    }

    // Check if payment link already exists
    const existingLink = await PaymentLink.findOne({ razorpayLinkId });
    if (existingLink) {
      return res.status(200).json({
        success: true,
        data: existingLink,
        message: 'Payment link already exists'
      });
    }

    // Create new payment link
    const paymentLink = new PaymentLink({
      razorpayLinkId,
      callId,
      phone,
      customerName: customerName || 'Customer',
      amount,
      amountDisplay: amountDisplay || (amount / 100),
      currency: currency || 'INR',
      productName,
      productId,
      shortUrl,
      description,
      whatsappMessageId,
      status: whatsappMessageId ? 'sent' : 'created',
      sentAt: whatsappMessageId ? new Date() : null,
      expiresAt: expiresAt ? new Date(expiresAt) : null,
      metadata: metadata || {}
    });

    await paymentLink.save();

    // Update call log if callId provided
    if (callId) {
      await CallLog.findOneAndUpdate(
        { callId },
        { 
          $push: { paymentLinks: paymentLink._id },
          $set: { 'metadata.hasPaymentLink': true }
        }
      );
    }

    // Emit socket event for real-time updates
    const io = req.app.get('io');
    if (io) {
      io.emit('paymentLink:created', paymentLink);
    }

    res.status(201).json({
      success: true,
      data: paymentLink
    });

  } catch (error) {
    console.error('Error creating payment link:', error);
    res.status(500).json({
      success: false,
      message: 'Error creating payment link',
      error: error.message
    });
  }
};

/**
 * Update payment link status
 * @route PATCH /api/payments/:id
 * @access Public (for bot/webhook integration)
 */
const updatePaymentLink = async (req, res) => {
  try {
    const { id } = req.params;
    const updateData = req.body;

    // Find by razorpayLinkId or MongoDB _id
    let paymentLink = await PaymentLink.findOne({ razorpayLinkId: id });
    if (!paymentLink) {
      paymentLink = await PaymentLink.findById(id);
    }

    if (!paymentLink) {
      return res.status(404).json({
        success: false,
        message: 'Payment link not found'
      });
    }

    // Update fields
    const allowedUpdates = [
      'status', 'whatsappStatus', 'whatsappMessageId',
      'paymentId', 'paymentMethod', 'error', 'metadata'
    ];

    allowedUpdates.forEach(field => {
      if (updateData[field] !== undefined) {
        paymentLink[field] = updateData[field];
      }
    });

    await paymentLink.save();

    // Emit socket event
    const io = req.app.get('io');
    if (io) {
      io.emit('paymentLink:updated', paymentLink);
    }

    res.json({
      success: true,
      data: paymentLink
    });

  } catch (error) {
    console.error('Error updating payment link:', error);
    res.status(500).json({
      success: false,
      message: 'Error updating payment link',
      error: error.message
    });
  }
};

/**
 * Get all payment links with pagination and filters
 * @route GET /api/payments
 * @access Private
 */
const getPaymentLinks = async (req, res) => {
  try {
    const {
      page = 1,
      limit = 20,
      status,
      productId,
      phone,
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

    if (productId) {
      query.productId = productId;
    }

    if (phone) {
      query.phone = { $regex: phone, $options: 'i' };
    }

    if (startDate || endDate) {
      query.createdAt = {};
      if (startDate) query.createdAt.$gte = new Date(startDate);
      if (endDate) query.createdAt.$lte = new Date(endDate);
    }

    // Execute query with pagination
    const skip = (parseInt(page) - 1) * parseInt(limit);
    const sort = { [sortBy]: sortOrder === 'desc' ? -1 : 1 };

    const [paymentLinks, total] = await Promise.all([
      PaymentLink.find(query)
        .sort(sort)
        .skip(skip)
        .limit(parseInt(limit))
        .lean(),
      PaymentLink.countDocuments(query)
    ]);

    res.json({
      success: true,
      data: paymentLinks,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
      }
    });

  } catch (error) {
    console.error('Error fetching payment links:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching payment links',
      error: error.message
    });
  }
};

/**
 * Get single payment link
 * @route GET /api/payments/:id
 * @access Private
 */
const getPaymentLink = async (req, res) => {
  try {
    const { id } = req.params;

    let paymentLink = await PaymentLink.findOne({ razorpayLinkId: id });
    if (!paymentLink) {
      paymentLink = await PaymentLink.findById(id);
    }

    if (!paymentLink) {
      return res.status(404).json({
        success: false,
        message: 'Payment link not found'
      });
    }

    res.json({
      success: true,
      data: paymentLink
    });

  } catch (error) {
    console.error('Error fetching payment link:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching payment link',
      error: error.message
    });
  }
};

/**
 * Get payment statistics
 * @route GET /api/payments/stats
 * @access Private
 */
const getPaymentStats = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;

    const [stats, productStats, dailyRevenue] = await Promise.all([
      PaymentLink.getPaymentStats(startDate, endDate),
      PaymentLink.getProductStats(),
      PaymentLink.getDailyRevenue(7)
    ]);

    res.json({
      success: true,
      data: {
        overview: stats,
        byProduct: productStats,
        dailyRevenue
      }
    });

  } catch (error) {
    console.error('Error fetching payment stats:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching payment stats',
      error: error.message
    });
  }
};

/**
 * Delete payment link
 * @route DELETE /api/payments/:id
 * @access Private (Admin only)
 */
const deletePaymentLink = async (req, res) => {
  try {
    const { id } = req.params;

    const paymentLink = await PaymentLink.findByIdAndDelete(id);

    if (!paymentLink) {
      return res.status(404).json({
        success: false,
        message: 'Payment link not found'
      });
    }

    // Remove reference from call log
    if (paymentLink.callId) {
      await CallLog.findOneAndUpdate(
        { callId: paymentLink.callId },
        { $pull: { paymentLinks: paymentLink._id } }
      );
    }

    res.json({
      success: true,
      message: 'Payment link deleted successfully'
    });

  } catch (error) {
    console.error('Error deleting payment link:', error);
    res.status(500).json({
      success: false,
      message: 'Error deleting payment link',
      error: error.message
    });
  }
};

/**
 * Get payment links for a specific call
 * @route GET /api/payments/call/:callId
 * @access Private
 */
const getPaymentsByCall = async (req, res) => {
  try {
    const { callId } = req.params;

    const paymentLinks = await PaymentLink.find({ callId })
      .sort({ createdAt: -1 })
      .lean();

    res.json({
      success: true,
      data: paymentLinks
    });

  } catch (error) {
    console.error('Error fetching payments for call:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching payments for call',
      error: error.message
    });
  }
};

module.exports = {
  createPaymentLink,
  updatePaymentLink,
  getPaymentLinks,
  getPaymentLink,
  getPaymentStats,
  deletePaymentLink,
  getPaymentsByCall
};

