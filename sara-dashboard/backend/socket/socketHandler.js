/**
 * Socket.io Handler
 * Real-time communication for live call updates
 */

const CallLog = require('../models/CallLog');

const socketHandler = (io) => {
  io.on('connection', (socket) => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] 🔌 User connected: ${socket.id}`);
    
    // Log to file
    const fs = require('fs');
    fs.appendFileSync('dashboard.log', `[${timestamp}] 🔌 User connected: ${socket.id}\n`, 'utf8');

    // Join user to their role-based room
    socket.on('join-room', (userRole) => {
      const timestamp = new Date().toISOString();
      console.log(`[${timestamp}] 👤 User ${socket.id} joined room: ${userRole}`);
      fs.appendFileSync('dashboard.log', `[${timestamp}] 👤 User ${socket.id} joined room: ${userRole}\n`, 'utf8');
      socket.join(userRole);
    });

    // Handle user actions
    socket.on('user-action', (action) => {
      const timestamp = new Date().toISOString();
      console.log(`[${timestamp}] 👆 User ${socket.id} action: ${action.type} - ${action.description}`);
      fs.appendFileSync('dashboard.log', `[${timestamp}] 👆 User ${socket.id} action: ${action.type} - ${action.description}\n`, 'utf8');
    });

    // Handle page navigation
    socket.on('page-navigation', (page) => {
      const timestamp = new Date().toISOString();
      console.log(`[${timestamp}] 🧭 User ${socket.id} navigated to: ${page}`);
      fs.appendFileSync('dashboard.log', `[${timestamp}] 🧭 User ${socket.id} navigated to: ${page}\n`, 'utf8');
    });

    // Handle call start event
    socket.on('call-started', async (callData) => {
      try {
        // Create call log entry
        const callLog = await CallLog.create({
          callId: callData.callId,
          type: callData.type || 'outbound',
          caller: callData.caller,
          receiver: callData.receiver,
          startTime: new Date(),
          status: 'in-progress',
          language: callData.language || 'en',
          metadata: {
            userAgent: callData.userAgent,
            ipAddress: callData.ipAddress,
            deviceType: callData.deviceType
          }
        });

        // Broadcast to all connected clients
        io.emit('call-started', {
          callId: callData.callId,
          caller: callData.caller,
          receiver: callData.receiver,
          startTime: callLog.startTime,
          status: 'in-progress'
        });

        console.log(`📞 Call started: ${callData.callId}`);
      } catch (error) {
        console.error('Error handling call start:', error);
        socket.emit('error', { message: 'Failed to log call start' });
      }
    });

    // Handle call end event
    socket.on('call-ended', async (callData) => {
      try {
        const callLog = await CallLog.findOne({ callId: callData.callId });
        
        if (callLog) {
          callLog.endTime = new Date();
          callLog.status = callData.status || 'success';
          callLog.transcript = callData.transcript || '';
          callLog.audioFile = callData.audioFile || '';
          callLog.interruptionCount = callData.interruptionCount || 0;
          callLog.satisfaction = callData.satisfaction || 'unknown';
          
          await callLog.save();

          // Broadcast to all connected clients
          io.emit('call-ended', {
            callId: callData.callId,
            status: callLog.status,
            duration: callLog.duration,
            endTime: callLog.endTime
          });

          console.log(`📞 Call ended: ${callData.callId} - Status: ${callLog.status}`);
        }
      } catch (error) {
        console.error('Error handling call end:', error);
        socket.emit('error', { message: 'Failed to log call end' });
      }
    });

    // Handle call update event
    socket.on('call-updated', async (callData) => {
      try {
        const callLog = await CallLog.findOne({ callId: callData.callId });
        
        if (callLog) {
          // Update specific fields
          if (callData.status) callLog.status = callData.status;
          if (callData.transcript) callLog.transcript = callData.transcript;
          if (callData.interruptionCount !== undefined) {
            callLog.interruptionCount = callData.interruptionCount;
          }
          
          await callLog.save();

          // Broadcast update to all connected clients
          io.emit('call-updated', {
            callId: callData.callId,
            status: callLog.status,
            interruptionCount: callLog.interruptionCount,
            transcript: callLog.transcript
          });

          console.log(`📞 Call updated: ${callData.callId}`);
        }
      } catch (error) {
        console.error('Error handling call update:', error);
        socket.emit('error', { message: 'Failed to update call' });
      }
    });

    // Handle call interruption event
    socket.on('call-interrupted', async (callData) => {
      try {
        const callLog = await CallLog.findOne({ callId: callData.callId });
        
        if (callLog) {
          callLog.interruptionCount = (callLog.interruptionCount || 0) + 1;
          await callLog.save();

          // Broadcast interruption to all connected clients
          io.emit('call-interrupted', {
            callId: callData.callId,
            interruptionCount: callLog.interruptionCount,
            timestamp: new Date()
          });

          console.log(`🛑 Call interrupted: ${callData.callId} (${callLog.interruptionCount} times)`);
        }
      } catch (error) {
        console.error('Error handling call interruption:', error);
        socket.emit('error', { message: 'Failed to log interruption' });
      }
    });

    // Handle system status updates
    socket.on('system-status', (statusData) => {
      // Broadcast system status to all connected clients
      io.emit('system-status-update', {
        status: statusData.status,
        message: statusData.message,
        timestamp: new Date()
      });

      console.log(`⚙️ System status update: ${statusData.status}`);
    });

    // Handle user activity
    socket.on('user-activity', (activityData) => {
      // Broadcast user activity to admin users
      socket.to('admin').emit('user-activity', {
        userId: activityData.userId,
        username: activityData.username,
        activity: activityData.activity,
        timestamp: new Date()
      });
    });

    // Handle disconnect
    socket.on('disconnect', () => {
      console.log(`🔌 User disconnected: ${socket.id}`);
    });

    // Handle errors
    socket.on('error', (error) => {
      console.error(`❌ Socket error for ${socket.id}:`, error);
    });
  });

  // Broadcast system health status every 30 seconds
  setInterval(async () => {
    try {
      const activeCalls = await CallLog.countDocuments({ status: 'in-progress' });
      const recentCalls = await CallLog.countDocuments({
        createdAt: { $gte: new Date(Date.now() - 5 * 60 * 1000) } // Last 5 minutes
      });

      io.emit('system-health', {
        activeCalls,
        recentCalls,
        timestamp: new Date(),
        uptime: process.uptime()
      });
    } catch (error) {
      console.error('Error broadcasting system health:', error);
    }
  }, 30000); // 30 seconds

  return io;
};

module.exports = socketHandler;
