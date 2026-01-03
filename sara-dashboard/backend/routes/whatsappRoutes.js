/**
 * WhatsApp Routes
 * API routes for WhatsApp message management
 */

const express = require('express');
const router = express.Router();
const {
  createMessage,
  updateMessage,
  getMessages,
  getMessage,
  getMessageStats,
  getMessagesByCall,
  deleteMessage
} = require('../controllers/whatsappController');

const { authMiddleware, authorize } = require('../middleware/authMiddleware');

// Public routes (for bot integration) - MUST come before auth middleware
router.post('/messages', createMessage);
router.patch('/messages/:id', updateMessage);

// Apply authentication to dashboard routes
router.use(authMiddleware);

// Protected dashboard routes
router.get('/stats', getMessageStats);
router.get('/call/:callId', getMessagesByCall);
router.get('/messages', getMessages);
router.get('/messages/:id', getMessage);

// Admin only routes
router.delete('/messages/:id', authorize('admin'), deleteMessage);

module.exports = router;

