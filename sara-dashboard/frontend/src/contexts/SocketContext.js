/**
 * Socket Context
 * Manages Socket.io connection and real-time updates
 */

import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from './AuthContext';
import { SOCKET_URL } from '../config/api';
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
  const socketRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 3; // Reduced attempts
  const socketDisabled = useRef(false); // Flag to disable socket permanently after failures
  const connectionTimeoutRef = useRef(null);
  
  // Check if Socket.io is disabled via environment variable
  const isSocketEnabled = process.env.REACT_APP_ENABLE_SOCKET !== 'false';

  // Initialize socket connection
  useEffect(() => {
    // Cleanup function
    const cleanup = () => {
      if (connectionTimeoutRef.current) {
        clearTimeout(connectionTimeoutRef.current);
        connectionTimeoutRef.current = null;
      }
      if (socketRef.current) {
        console.log('🧹 Cleaning up socket connection');
        socketRef.current.removeAllListeners();
        socketRef.current.close();
        socketRef.current = null;
        setSocket(null);
        setIsConnected(false);
      }
    };

    // Don't try to connect if socket is disabled
    if (!isSocketEnabled || socketDisabled.current) {
      if (!isSocketEnabled) {
        console.log('⚠️ Socket.io disabled via environment variable');
      } else {
        console.log('⚠️ Socket.io disabled due to previous failures');
      }
      return cleanup;
    }

    if (isAuthenticated && user) {
      // Don't create new socket if one already exists and is connected
      if (socketRef.current) {
        if (socketRef.current.connected) {
          return cleanup;
        }
        // If socket exists but not connected, clean it up first
        cleanup();
      }

      console.log('🔌 Initializing socket connection');
      
      // Set a timeout to disable socket if connection takes too long
      connectionTimeoutRef.current = setTimeout(() => {
        if (socketRef.current && !socketRef.current.connected) {
          console.error('⏱️ Socket connection timeout - disabling');
          socketDisabled.current = true;
          cleanup();
        }
      }, 10000); // 10 second timeout

      const newSocket = io(SOCKET_URL, {
        auth: {
          token: localStorage.getItem('token')
        },
        reconnection: true,
        reconnectionDelay: 2000, // Increased delay
        reconnectionDelayMax: 10000, // Max 10 seconds
        reconnectionAttempts: maxReconnectAttempts,
        timeout: 5000, // Connection timeout
        transports: ['polling'], // Start with polling only, upgrade to websocket if available
        upgrade: true,
        rememberUpgrade: false
      });

      socketRef.current = newSocket;
      setSocket(newSocket);

      // Connection event handlers
      newSocket.on('connect', () => {
        if (connectionTimeoutRef.current) {
          clearTimeout(connectionTimeoutRef.current);
          connectionTimeoutRef.current = null;
        }
        console.log('🔌 Connected to server');
        setIsConnected(true);
        reconnectAttempts.current = 0;
        
        // Join role-based room
        newSocket.emit('join-room', user.role);
      });

      newSocket.on('disconnect', (reason) => {
        console.log('🔌 Disconnected from server:', reason);
        setIsConnected(false);
        
        // Don't reconnect if user logged out or server disconnected
        if (reason === 'io server disconnect' || reason === 'transport close' || !isAuthenticated) {
          cleanup();
        }
      });

      newSocket.on('connect_error', (error) => {
        reconnectAttempts.current += 1;
        console.error('❌ Socket connection error:', error.message);
        setIsConnected(false);
        
        // Disable socket after max attempts to prevent resource exhaustion
        if (reconnectAttempts.current >= maxReconnectAttempts) {
          console.error('❌ Max reconnection attempts reached - disabling Socket.io');
          socketDisabled.current = true;
          if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
            connectionTimeoutRef.current = null;
          }
          cleanup();
          // Don't show error toast - app works without socket
          console.warn('⚠️ Socket.io disabled. App will continue without real-time updates.');
        }
      });

      // Handle reconnection attempts
      newSocket.io.on('reconnect_attempt', (attemptNumber) => {
        console.log(`🔄 Socket reconnection attempt ${attemptNumber}/${maxReconnectAttempts}`);
        if (attemptNumber >= maxReconnectAttempts) {
          socketDisabled.current = true;
          cleanup();
        }
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

      newSocket.on('transcript-updated', (data) => {
        console.log('📝 Transcript updated:', data);
        setActiveCalls(prev => 
          prev.map(call => 
            call.callId === data.callId 
              ? { ...call, transcript: (call.transcript || '') + `${data.speaker}: ${data.text}\n` }
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

      return cleanup;
    } else {
      // Disconnect socket if user is not authenticated
      cleanup();
      socketDisabled.current = false; // Reset on logout
      reconnectAttempts.current = 0;
      return () => {};
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, user?._id]); // Only depend on user ID, not entire user object

  // Reset socket disabled flag when user changes (new login)
  useEffect(() => {
    if (isAuthenticated && user) {
      socketDisabled.current = false;
      reconnectAttempts.current = 0;
    }
  }, [user?._id, isAuthenticated]);

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
