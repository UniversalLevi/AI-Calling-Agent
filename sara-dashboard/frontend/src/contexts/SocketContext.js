/**
 * Socket Context
 * Manages Socket.io connection and real-time updates
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

// Create context
const SocketContext = createContext();

// Socket provider component
export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [activeCalls, setActiveCalls] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const { isAuthenticated, user } = useAuth();

  // Initialize socket connection
  useEffect(() => {
    if (isAuthenticated && user) {
      const newSocket = io(process.env.REACT_APP_SOCKET_URL || 'http://localhost:5000', {
        auth: {
          token: localStorage.getItem('token')
        }
      });

      setSocket(newSocket);

      // Connection event handlers
      newSocket.on('connect', () => {
        console.log('🔌 Connected to server');
        setIsConnected(true);
        
        // Join role-based room
        newSocket.emit('join-room', user.role);
      });

      newSocket.on('disconnect', () => {
        console.log('🔌 Disconnected from server');
        setIsConnected(false);
      });

      newSocket.on('connect_error', (error) => {
        console.error('❌ Socket connection error:', error);
        setIsConnected(false);
      });

      // Call event handlers
      newSocket.on('call-started', (callData) => {
        console.log('📞 Call started:', callData);
        setActiveCalls(prev => [...prev, callData]);
        
        toast.success(`New call started: ${callData.caller} → ${callData.receiver}`, {
          duration: 5000
        });
      });

      newSocket.on('call-ended', (callData) => {
        console.log('📞 Call ended:', callData);
        setActiveCalls(prev => 
          prev.filter(call => call.callId !== callData.callId)
        );
        
        toast.success(`Call ended: ${callData.callId}`, {
          duration: 3000
        });
      });

      newSocket.on('call-updated', (callData) => {
        console.log('📞 Call updated:', callData);
        setActiveCalls(prev => 
          prev.map(call => 
            call.callId === callData.callId 
              ? { ...call, ...callData }
              : call
          )
        );
      });

      newSocket.on('call-interrupted', (callData) => {
        console.log('🛑 Call interrupted:', callData);
        
        toast.info(`Call interrupted: ${callData.callId}`, {
          duration: 3000
        });
      });

      newSocket.on('call-terminated', (callData) => {
        console.log('🛑 Call terminated:', callData);
        setActiveCalls(prev => 
          prev.filter(call => call.callId !== callData.callId)
        );
        
        toast.warning(`Call terminated: ${callData.callId}`, {
          duration: 4000
        });
      });

      // System event handlers
      newSocket.on('system-health', (healthData) => {
        console.log('⚙️ System health update:', healthData);
        setSystemHealth(healthData);
      });

      newSocket.on('system-status-update', (statusData) => {
        console.log('⚙️ System status update:', statusData);
        
        const statusMessages = {
          'healthy': 'System is running smoothly',
          'warning': 'System experiencing minor issues',
          'critical': 'System experiencing critical issues'
        };
        
        const message = statusMessages[statusData.status] || statusData.message;
        
        if (statusData.status === 'critical') {
          toast.error(message, { duration: 10000 });
        } else if (statusData.status === 'warning') {
          toast.warning(message, { duration: 7000 });
        } else {
          toast.success(message, { duration: 5000 });
        }
      });

      newSocket.on('user-activity', (activityData) => {
        console.log('👤 User activity:', activityData);
        
        if (user.role === 'admin') {
          toast.info(`${activityData.username}: ${activityData.activity}`, {
            duration: 3000
          });
        }
      });

      // Error handler
      newSocket.on('error', (error) => {
        console.error('❌ Socket error:', error);
        toast.error('Connection error occurred');
      });

      return () => {
        newSocket.close();
      };
    } else {
      // Disconnect socket if user is not authenticated
      if (socket) {
        socket.close();
        setSocket(null);
        setIsConnected(false);
      }
    }
  }, [isAuthenticated, user]);

  // Emit call termination
  const terminateCall = (callId) => {
    if (socket && isConnected) {
      socket.emit('call-terminated', { callId });
    }
  };

  // Emit system status update
  const updateSystemStatus = (status, message) => {
    if (socket && isConnected) {
      socket.emit('system-status', { status, message });
    }
  };

  // Emit user activity
  const emitUserActivity = (activity) => {
    if (socket && isConnected && user) {
      socket.emit('user-activity', {
        userId: user._id,
        username: user.username,
        activity
      });
    }
  };

  // Track user actions
  const trackUserAction = (type, description) => {
    if (socket && isConnected) {
      socket.emit('user-action', { type, description, timestamp: new Date().toISOString() });
    }
  };

  // Track page navigation
  const trackPageNavigation = (page) => {
    if (socket && isConnected) {
      socket.emit('page-navigation', page);
    }
  };

  const value = {
    socket,
    isConnected,
    activeCalls,
    systemHealth,
    terminateCall,
    updateSystemStatus,
    emitUserActivity,
    trackUserAction,
    trackPageNavigation
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
};

// Custom hook to use socket context
export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};

export default SocketContext;
