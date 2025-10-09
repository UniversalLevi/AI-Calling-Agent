/**
 * Dashboard Page - Main Overview
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { useSocket } from '../../contexts/SocketContext';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Dashboard = () => {
  const { user, token } = useAuth();
  const { isConnected } = useSocket();
  const [stats, setStats] = useState(null);
  const [activeCalls, setActiveCalls] = useState([]);
  const [recentCalls, setRecentCalls] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token && user) {
      fetchDashboardData();
        const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30s
      return () => clearInterval(interval);
    }
  }, [token, user]);

  const fetchDashboardData = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    
    try {
      // Only show loading on initial load, not on refreshes
      if (stats.totalCalls === 0 && activeCalls.length === 0 && recentCalls.length === 0) {
        setLoading(true);
      }
      
      const [statsRes, activeRes, recentRes] = await Promise.all([
        axios.get(`${API_URL}/calls/stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/calls/active`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/calls?limit=5&sortBy=createdAt&sortOrder=desc`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      // Only update state if data has changed to prevent unnecessary re-renders
      if (statsRes.data.success && JSON.stringify(statsRes.data.data) !== JSON.stringify(stats)) {
        setStats(statsRes.data.data);
      }
      if (activeRes.data.success && JSON.stringify(activeRes.data.data) !== JSON.stringify(activeCalls)) {
        setActiveCalls(activeRes.data.data);
      }
      if (recentRes.data.success && JSON.stringify(recentRes.data.data) !== JSON.stringify(recentCalls)) {
        setRecentCalls(recentRes.data.data);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      // Don't clear data on error, keep existing data
      // Only show error if it's a critical error (not 401/403)
      if (err.response?.status !== 401 && err.response?.status !== 403) {
        console.warn('Dashboard data fetch failed, keeping existing data');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '--';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="fade-in">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-600">
          Welcome back, {user?.firstName} {user?.lastName}!
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Calls
                </dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {stats?.totalCalls || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Successful
                </dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {stats?.successfulCalls || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-yellow-500 rounded-md p-3">
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Avg Duration
                </dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {formatDuration(Math.floor(stats?.averageDuration || 0))}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className={`flex-shrink-0 ${activeCalls.length > 0 ? 'bg-red-500 animate-pulse' : 'bg-gray-400'} rounded-md p-3`}>
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Active Calls
                </dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {activeCalls.length}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Calls */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recent Calls
          </h2>
          {recentCalls.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No recent calls</p>
          ) : (
            <div className="space-y-4">
              {recentCalls.map((call) => (
                <div key={call._id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {call.caller} → {call.receiver}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatDate(call.startTime)}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">
                      {formatDuration(call.duration)}
                    </span>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      call.status === 'success' ? 'bg-green-100 text-green-800' :
                      call.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {call.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* System Status */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            System Status
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Backend API</span>
              <span className="flex items-center text-sm font-medium text-green-600">
                <span className="h-2 w-2 bg-green-500 rounded-full mr-2"></span>
                Connected
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Real-time Updates</span>
              <span className={`flex items-center text-sm font-medium ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                <span className={`h-2 w-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'} rounded-full mr-2`}></span>
                {isConnected ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">User Role</span>
              <span className="text-sm font-medium text-gray-900 capitalize">
                {user?.role}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Success Rate</span>
              <span className="text-sm font-medium text-gray-900">
                {stats?.successRate || 0}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card mt-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <a href="/calls" className="btn-primary text-center">
            View All Calls
          </a>
          <a href="/live" className="btn-primary text-center">
            Monitor Live Calls
          </a>
          <a href="/analytics" className="btn-primary text-center">
            View Analytics
          </a>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;