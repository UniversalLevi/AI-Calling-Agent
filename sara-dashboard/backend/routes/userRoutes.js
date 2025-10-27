/**
 * User Routes
 * API routes for user management and authentication
 */

const express = require('express');
const router = express.Router();
const {
  registerUser,
  loginUser,
  getProfile,
  updateProfile,
  changePassword,
  getUsers,
  getUser,
  updateUser,
  deleteUser,
  getUserStats
} = require('../controllers/userController');

const { authMiddleware, authorize, requirePermission } = require('../middleware/authMiddleware');

// Public routes (no authentication required)
router.post('/login', loginUser);

// Protected routes (authentication required)
router.use(authMiddleware);

// @route   GET /api/users/profile
// @desc    Get current user profile
// @access  Private
router.get('/profile', getProfile);

// @route   PUT /api/users/profile
// @desc    Update current user profile
// @access  Private
router.put('/profile', updateProfile);

// @route   PUT /api/users/change-password
// @desc    Change user password
// @access  Private
router.put('/change-password', changePassword);

// Admin only routes
router.use(authorize('admin'));

// @route   POST /api/users/register
// @desc    Register new user
// @access  Private (Admin only)
router.post('/register', registerUser);

// @route   GET /api/users
// @desc    Get all users
// @access  Private (Admin only)
router.get('/', getUsers);

// @route   GET /api/users/stats
// @desc    Get user statistics
// @access  Private (Admin only)
router.get('/stats', getUserStats);

// @route   GET /api/users/:id
// @desc    Get user by ID
// @access  Private (Admin only)
router.get('/:id', getUser);

// @route   PUT /api/users/:id
// @desc    Update user
// @access  Private (Admin only)
router.put('/:id', updateUser);

// @route   DELETE /api/users/:id
// @desc    Delete user
// @access  Private (Admin only)
router.delete('/:id', deleteUser);

module.exports = router;
