/**
 * Live Calls Page - Real-time monitoring
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { useSocket } from '../../contexts/SocketContext';

const LiveCalls = () => {
  const { token } = useAuth();
  const { socket, isConnected } = useSocket();
  const [activeCalls, setActiveCalls] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchActiveCalls = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get('/calls/active', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data.success) {
        setActiveCalls(response.data.data);
        console.log('✅ Active calls fetched:', response.data.data);
      } else {
        console.log('⚠️ No active calls found');
        setActiveCalls([]);
      }
    } catch (err) {
      console.error('Error fetching active calls:', err);
      setActiveCalls([]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchActiveCalls();
  }, [fetchActiveCalls]);

  useEffect(() => {
    if (!socket || !isConnected) return;

    // Listen for real-time updates
    socket.on('callStarted', (data) => {
      console.log('New call started:', data);
      fetchActiveCalls();
    });

    socket.on('callUpdated', (data) => {
      console.log('Call updated:', data);
      fetchActiveCalls();
    });

    socket.on('callTerminated', (data) => {
      console.log('Call terminated:', data);
      fetchActiveCalls();
    });

    return () => {
      socket.off('callStarted');
      socket.off('callUpdated');
      socket.off('callTerminated');
    };
  }, [socket, isConnected, fetchActiveCalls]);

  const formatDuration = (startTime) => {
    if (!startTime) return '0:00';
    const start = new Date(startTime);
    const now = new Date();
    const diff = Math.floor((now - start) / 1000);
    const mins = Math.floor(diff / 60);
    const secs = diff % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="fade-in">
        <h1 className="text-3xl font-bold text-dark-text mb-6">Live Calls</h1>
        <div className="card">
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-dark-text">Live Calls</h1>
          <p className="mt-2 text-sm text-gray-300">
            Monitor active calls in real-time
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`h-3 w-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-300">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Active Calls Count */}
      <div className="card mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-dark-text">Active Calls</h3>
            <p className="text-sm text-gray-300">Currently in progress</p>
          </div>
          <div className="text-4xl font-bold text-blue-600">
            {activeCalls.length}
          </div>
        </div>
      </div>

      {/* Active Calls List */}
      {activeCalls.length === 0 ? (
        <div className="card">
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-dark-text">No active calls</h3>
            <p className="mt-1 text-sm text-gray-400">
              Active calls will appear here in real-time
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {activeCalls.map((call) => (
            <div key={call._id} className="card border-l-4 border-blue-500">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                    <h3 className="text-lg font-semibold text-dark-text">
                      Call in Progress
                    </h3>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div>
                      <p className="text-sm text-gray-400">Caller</p>
                      <p className="text-base font-medium text-dark-text">{call.caller}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400">Receiver</p>
                      <p className="text-base font-medium text-dark-text">{call.receiver}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400">Duration</p>
                      <p className="text-base font-medium text-dark-text">{formatDuration(call.startTime)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400">Language</p>
                      <p className="text-base font-medium text-dark-text capitalize">{call.language}</p>
                    </div>
                  </div>

                  {call.transcript && (
                    <div className="mt-4">
                      <p className="text-sm text-gray-400 mb-2">Transcript</p>
                      <div className="bg-gray-700 rounded p-3 max-h-40 overflow-y-auto">
                        <pre className="text-sm text-gray-200 whitespace-pre-wrap font-sans">
                          {call.transcript}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="ml-4">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-900 text-blue-200">
                    {call.type}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LiveCalls;