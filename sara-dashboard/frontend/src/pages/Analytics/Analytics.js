/**
 * Analytics Page
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Analytics = () => {
  const { token } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [period, setPeriod] = useState('7d');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/calls/analytics?period=${period}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data.success) {
        setAnalytics(response.data.data);
      }
    } catch (err) {
      console.error('Error fetching analytics:', err);
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

  if (loading) {
    return (
      <div className="fade-in">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Analytics</h1>
        <div className="card">
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  const stats = analytics?.totalStats || {};

  return (
    <div className="fade-in">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="mt-2 text-sm text-gray-600">
            Detailed insights and statistics
          </p>
        </div>
        <div>
          <select
            className="input-field"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
          >
            <option value="1d">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Total Calls</h3>
          <p className="mt-2 text-3xl font-semibold text-gray-900">
            {stats.totalCalls || 0}
          </p>
        </div>

        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Successful</h3>
          <p className="mt-2 text-3xl font-semibold text-green-600">
            {stats.successfulCalls || 0}
          </p>
        </div>

        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Failed</h3>
          <p className="mt-2 text-3xl font-semibold text-red-600">
            {stats.failedCalls || 0}
          </p>
        </div>

        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Missed</h3>
          <p className="mt-2 text-3xl font-semibold text-yellow-600">
            {stats.missedCalls || 0}
          </p>
        </div>
      </div>

      {/* Duration Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 mb-8">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Average Duration</h3>
          <p className="text-3xl font-semibold text-gray-900">
            {formatDuration(Math.floor(stats.averageDuration || 0))}
          </p>
        </div>

        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Duration</h3>
          <p className="text-3xl font-semibold text-gray-900">
            {formatDuration(Math.floor(stats.totalDuration || 0))}
          </p>
        </div>
      </div>

      {/* Language Distribution */}
      {analytics?.languageDistribution && analytics.languageDistribution.length > 0 && (
        <div className="card mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Language Distribution
          </h2>
          <div className="space-y-4">
            {analytics.languageDistribution.map((lang) => (
              <div key={lang._id} className="flex items-center">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {lang._id === 'en' ? 'English' : lang._id === 'hi' ? 'Hindi' : lang._id === 'mixed' ? 'Hinglish' : lang._id}
                    </span>
                    <span className="text-sm text-gray-500">{lang.count} calls</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${(lang.count / stats.totalCalls) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status Distribution */}
      {analytics?.statusDistribution && analytics.statusDistribution.length > 0 && (
        <div className="card mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Status Distribution
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {analytics.statusDistribution.map((status) => (
              <div key={status._id} className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">{status.count}</p>
                <p className="text-sm text-gray-600 capitalize mt-1">{status._id}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hourly Distribution */}
      {analytics?.hourlyDistribution && analytics.hourlyDistribution.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Hourly Distribution
          </h2>
          <div className="space-y-2">
            {analytics.hourlyDistribution.map((hour) => (
              <div key={hour._id} className="flex items-center">
                <span className="text-sm text-gray-600 w-16">
                  {hour._id}:00
                </span>
                <div className="flex-1 ml-4">
                  <div className="w-full bg-gray-200 rounded-full h-6">
                    <div
                      className="bg-green-500 h-6 rounded-full flex items-center justify-end pr-2"
                      style={{ width: `${(hour.count / Math.max(...analytics.hourlyDistribution.map(h => h.count))) * 100}%` }}
                    >
                      <span className="text-xs text-white font-medium">{hour.count}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;