/**
 * Dashboard Page - Main Overview
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { useSocket } from '../../contexts/SocketContext';
import { API_URL } from '../../config/api';

const Dashboard = () => {
  const { user, token } = useAuth();
  const { isConnected } = useSocket();
  const [stats, setStats] = useState(null);
  const [activeCalls, setActiveCalls] = useState([]);
  const [recentCalls, setRecentCalls] = useState([]);
  const [paymentStats, setPaymentStats] = useState(null);
  const [whatsappStats, setWhatsappStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);

  const fetchDashboardData = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    
    try {
      // Only show loading on initial load, not on refreshes
      if (!stats || (stats.totalCalls === 0 && activeCalls.length === 0 && recentCalls.length === 0)) {
        setLoading(true);
      }
      
      const [statsRes, activeRes, recentRes, paymentRes, whatsappRes] = await Promise.all([
        axios.get(`${API_URL}/calls/stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/calls/active`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/calls?limit=5&sortBy=createdAt&sortOrder=desc`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/payments/stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).catch(() => ({ data: { success: false } })),
        axios.get(`${API_URL}/whatsapp/stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).catch(() => ({ data: { success: false } }))
      ]);

      // Reset retry count on successful fetch
      setRetryCount(0);
      
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
      if (paymentRes.data.success) {
        setPaymentStats(paymentRes.data.data);
      }
      if (whatsappRes.data.success) {
        setWhatsappStats(whatsappRes.data.data);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      
      // Handle specific error types
      if (err.response?.status === 401) {
        // Token expired or invalid, logout user
        console.log('Token expired, logging out...');
        window.location.href = '/login';
        return;
      }
      
      if (err.response?.status === 403) {
        // Insufficient permissions
        console.warn('Insufficient permissions for dashboard data');
        return;
      }
      
      // Retry mechanism for network errors
      if (retryCount < 3 && (err.code === 'NETWORK_ERROR' || !err.response)) {
        console.log(`Retrying dashboard data fetch (attempt ${retryCount + 1}/3)...`);
        setRetryCount(prev => prev + 1);
        setTimeout(() => fetchDashboardData(), 2000 * (retryCount + 1)); // Exponential backoff
        return;
      }
      
      // Network or server errors - keep existing data
      if (err.code === 'NETWORK_ERROR' || err.response?.status >= 500) {
        console.warn('Network/server error, keeping existing data');
        return;
      }
      
      // Only show error if it's a critical error (not 401/403)
      if (err.response?.status !== 401 && err.response?.status !== 403) {
        console.warn('Dashboard data fetch failed, keeping existing data');
      }
    } finally {
      setLoading(false);
    }
  }, [token, stats, activeCalls, recentCalls, retryCount]);

  useEffect(() => {
    if (token && user) {
      fetchDashboardData();
      const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30s
      return () => clearInterval(interval);
    }
  }, [token, user, fetchDashboardData]);

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
        <h1 className="text-heading-lg font-bold text-dark-text">Dashboard</h1>
        <p className="mt-2 text-sm text-dark-text-muted">
          Welcome back, {user?.firstName} {user?.lastName}!
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-6 mb-8">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
              <svg className="h-6 w-6 text-dark-text" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-dark-text-muted truncate">
                  Total Calls
                </dt>
                <dd className="text-2xl font-semibold text-dark-text">
                  {stats?.totalCalls || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
              <svg className="h-6 w-6 text-dark-text" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-dark-text-muted truncate">
                  Successful
                </dt>
                <dd className="text-2xl font-semibold text-dark-text">
                  {stats?.successfulCalls || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-yellow-500 rounded-md p-3">
              <svg className="h-6 w-6 text-dark-text" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-dark-text-muted truncate">
                  Avg Duration
                </dt>
                <dd className="text-2xl font-semibold text-dark-text">
                  {formatDuration(Math.floor(stats?.averageDuration || 0))}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className={`flex-shrink-0 ${activeCalls.length > 0 ? 'bg-red-500 animate-pulse' : 'bg-gray-400'} rounded-md p-3`}>
              <svg className="h-6 w-6 text-dark-text" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-dark-text-muted truncate">
                  Active Calls
                </dt>
                <dd className="text-2xl font-semibold text-dark-text">
                  {activeCalls.length}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        {/* Revenue Card */}
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-emerald-500 rounded-md p-3">
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-dark-text-muted truncate">
                  Revenue
                </dt>
                <dd className="text-2xl font-semibold text-emerald-500">
                  ₹{paymentStats?.overview?.totalRevenue?.toLocaleString() || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        {/* WhatsApp Delivery Card */}
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-dark-text-muted truncate">
                  WhatsApp
                </dt>
                <dd className="text-2xl font-semibold text-green-500">
                  {whatsappStats?.overview?.deliveryRate || 0}%
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
          <h2 className="text-lg font-semibold text-dark-text mb-4">
            Recent Calls
          </h2>
          {recentCalls.length === 0 ? (
            <p className="text-dark-text-muted text-center py-8">No recent calls</p>
          ) : (
            <div className="space-y-4">
              {recentCalls.map((call) => (
                <div key={call._id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-dark-text">
                      {call.caller} → {call.receiver}
                    </p>
                    <p className="text-xs text-dark-text-muted">
                      {formatDate(call.startTime)}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-dark-text-muted">
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
          <h2 className="text-lg font-semibold text-dark-text mb-4">
            System Status
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-dark-text-muted">Backend API</span>
              <span className="flex items-center text-sm font-medium text-green-600">
                <span className="h-2 w-2 bg-green-500 rounded-full mr-2"></span>
                Connected
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-dark-text-muted">Real-time Updates</span>
              <span className={`flex items-center text-sm font-medium ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                <span className={`h-2 w-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'} rounded-full mr-2`}></span>
                {isConnected ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-dark-text-muted">User Role</span>
              <span className="text-sm font-medium text-dark-text capitalize">
                {user?.role}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-dark-text-muted">Success Rate</span>
              <span className="text-sm font-medium text-dark-text">
                {stats?.successRate || 0}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-dark-text-muted">Payment Conversion</span>
              <span className="text-sm font-medium text-emerald-500">
                {paymentStats?.overview?.conversionRate || 0}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-dark-text-muted">Pending Payments</span>
              <span className="text-sm font-medium text-yellow-500">
                {paymentStats?.overview?.pendingLinks || 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card mt-8">
        <h2 className="text-lg font-semibold text-dark-text mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
          <a href="/calls" className="btn-primary text-center">
            View All Calls
          </a>
          <a href="/live-calls" className="btn-primary text-center">
            Monitor Live Calls
          </a>
          <a href="/payments" className="btn-primary text-center bg-emerald-600 hover:bg-emerald-700">
            View Payments
          </a>
          <a href="/whatsapp" className="btn-primary text-center bg-green-600 hover:bg-green-700">
            WhatsApp Messages
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