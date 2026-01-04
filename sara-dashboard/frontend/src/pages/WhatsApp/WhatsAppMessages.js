/**
 * WhatsApp Messages Page
 * Dashboard for viewing WhatsApp message logs and delivery status
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { useSocket } from '../../contexts/SocketContext';
import { API_URL } from '../../config/api';

const WhatsAppMessages = () => {
  const { token } = useAuth();
  const { socket } = useSocket();
  const [messages, setMessages] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 });
  const [filters, setFilters] = useState({
    status: '',
    type: '',
    startDate: '',
    endDate: ''
  });

  const fetchMessages = useCallback(async () => {
    try {
      const params = new URLSearchParams({
        page: pagination.page,
        limit: pagination.limit,
        ...(filters.status && { status: filters.status }),
        ...(filters.type && { type: filters.type }),
        ...(filters.startDate && { startDate: filters.startDate }),
        ...(filters.endDate && { endDate: filters.endDate })
      });

      const response = await axios.get(`${API_URL}/whatsapp/messages?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setMessages(response.data.data);
        setPagination(prev => ({ ...prev, ...response.data.pagination }));
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setLoading(false);
    }
  }, [token, pagination.page, pagination.limit, filters]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/whatsapp/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setStats(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching WhatsApp stats:', error);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchMessages();
      fetchStats();
    }
  }, [token, fetchMessages, fetchStats, pagination.page, filters]);

  useEffect(() => {
    if (socket) {
      socket.on('whatsapp:messageSent', (message) => {
        setMessages(prev => [message, ...prev]);
        fetchStats();
      });
      socket.on('whatsapp:statusUpdate', (message) => {
        setMessages(prev => prev.map(m => 
          m.messageId === message.messageId ? message : m
        ));
        fetchStats();
      });
      return () => {
        socket.off('whatsapp:messageSent');
        socket.off('whatsapp:statusUpdate');
      };
    }
  }, [socket, fetchStats]);

  const formatDate = (dateString) => {
    if (!dateString) return '--';
    return new Date(dateString).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    const statusStyles = {
      pending: 'bg-gray-100 text-gray-800',
      sent: 'bg-blue-100 text-blue-800',
      delivered: 'bg-green-100 text-green-800',
      read: 'bg-emerald-100 text-emerald-800',
      failed: 'bg-red-100 text-red-800'
    };

    const statusIcons = {
      pending: '⏳',
      sent: '✓',
      delivered: '✓✓',
      read: '👁',
      failed: '✗'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusStyles[status] || 'bg-gray-100 text-gray-800'}`}>
        {statusIcons[status]} {status?.charAt(0).toUpperCase() + status?.slice(1)}
      </span>
    );
  };

  const getTypeBadge = (type) => {
    const typeStyles = {
      text: 'bg-gray-600 text-gray-100',
      template: 'bg-purple-600 text-purple-100',
      payment_link: 'bg-green-600 text-green-100',
      image: 'bg-blue-600 text-blue-100',
      document: 'bg-yellow-600 text-yellow-100'
    };

    const typeLabels = {
      text: 'Text',
      template: 'Template',
      payment_link: 'Payment',
      image: 'Image',
      document: 'Document'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded ${typeStyles[type] || 'bg-gray-600 text-gray-100'}`}>
        {typeLabels[type] || type}
      </span>
    );
  };

  const maskPhone = (phone) => {
    if (!phone) return '--';
    if (phone.length <= 4) return '****';
    return phone.slice(0, -4).replace(/./g, '*') + phone.slice(-4);
  };

  const truncateContent = (content, maxLength = 50) => {
    if (!content) return '--';
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  if (loading) {
    return (
      <div className="fade-in">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div className="mb-8">
        <h1 className="text-heading-lg font-bold text-dark-text">WhatsApp Messages</h1>
        <p className="mt-2 text-sm text-dark-text-muted">
          Track all WhatsApp messages sent during calls
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5 mb-8">
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-dark-text-muted">Total Sent</p>
                <p className="text-2xl font-semibold text-dark-text">{stats.overview?.totalMessages || 0}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-dark-text-muted">Delivered</p>
                <p className="text-2xl font-semibold text-blue-500">{stats.overview?.deliveredMessages || 0}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-emerald-500 rounded-md p-3">
                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-dark-text-muted">Read</p>
                <p className="text-2xl font-semibold text-emerald-500">{stats.overview?.readMessages || 0}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-red-500 rounded-md p-3">
                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-dark-text-muted">Failed</p>
                <p className="text-2xl font-semibold text-red-500">{stats.overview?.failedMessages || 0}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-purple-500 rounded-md p-3">
                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-dark-text-muted">Delivery Rate</p>
                <p className="text-2xl font-semibold text-purple-500">{stats.overview?.deliveryRate || 0}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          <select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="bg-dark-card border border-dark-border rounded-md px-3 py-2 text-dark-text focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="sent">Sent</option>
            <option value="delivered">Delivered</option>
            <option value="read">Read</option>
            <option value="failed">Failed</option>
          </select>

          <select
            value={filters.type}
            onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value }))}
            className="bg-dark-card border border-dark-border rounded-md px-3 py-2 text-dark-text focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="">All Types</option>
            <option value="text">Text</option>
            <option value="template">Template</option>
            <option value="payment_link">Payment Link</option>
          </select>

          <input
            type="date"
            value={filters.startDate}
            onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
            className="bg-dark-card border border-dark-border rounded-md px-3 py-2 text-dark-text focus:outline-none focus:ring-2 focus:ring-green-500"
          />

          <input
            type="date"
            value={filters.endDate}
            onChange={(e) => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
            className="bg-dark-card border border-dark-border rounded-md px-3 py-2 text-dark-text focus:outline-none focus:ring-2 focus:ring-green-500"
          />

          <button
            onClick={() => setFilters({ status: '', type: '', startDate: '', endDate: '' })}
            className="px-4 py-2 text-sm text-dark-text-muted hover:text-dark-text transition-colors"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Messages Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-dark-border">
            <thead className="bg-dark-card">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Recipient
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Content
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Sent At
                </th>
              </tr>
            </thead>
            <tbody className="bg-dark-sidebar divide-y divide-dark-border">
              {messages.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-dark-text-muted">
                    No messages found
                  </td>
                </tr>
              ) : (
                messages.map((message) => (
                  <tr key={message._id || message.messageId} className="hover:bg-dark-hover transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <p className="text-sm font-medium text-dark-text">{message.customerName || 'Customer'}</p>
                        <p className="text-xs text-dark-text-muted">{maskPhone(message.phone)}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getTypeBadge(message.type)}
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm text-dark-text max-w-xs truncate" title={message.content}>
                        {truncateContent(message.content)}
                      </p>
                      {message.paymentLinkUrl && (
                        <a
                          href={message.paymentLinkUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-500 hover:text-blue-400"
                        >
                          View Payment Link
                        </a>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(message.status)}
                      {message.error?.needsOptin && (
                        <p className="text-xs text-red-400 mt-1">Opt-in required</p>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <p className="text-sm text-dark-text-muted">{formatDate(message.sentAt || message.createdAt)}</p>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pagination.pages > 1 && (
          <div className="px-6 py-4 border-t border-dark-border flex items-center justify-between">
            <p className="text-sm text-dark-text-muted">
              Showing {((pagination.page - 1) * pagination.limit) + 1} to {Math.min(pagination.page * pagination.limit, pagination.total)} of {pagination.total}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                disabled={pagination.page === 1}
                className="px-3 py-1 rounded bg-dark-card text-dark-text disabled:opacity-50 disabled:cursor-not-allowed hover:bg-dark-hover"
              >
                Previous
              </button>
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={pagination.page === pagination.pages}
                className="px-3 py-1 rounded bg-dark-card text-dark-text disabled:opacity-50 disabled:cursor-not-allowed hover:bg-dark-hover"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WhatsAppMessages;

