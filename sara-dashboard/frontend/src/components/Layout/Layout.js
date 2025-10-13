/**
 * Layout Component
 * Main layout wrapper with sidebar and navigation
 */

import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useSocket } from '../../contexts/SocketContext';

// Components
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import LoadingSpinner from '../Common/LoadingSpinner';

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isLoading } = useAuth();
  const { isConnected, trackPageNavigation } = useSocket();
  const location = useLocation();

  // Track page navigation
  useEffect(() => {
    if (trackPageNavigation) {
      const pageName = location.pathname.split('/').pop() || 'dashboard';
      trackPageNavigation(pageName);
    }
  }, [location.pathname, trackPageNavigation]);

  // Show loading spinner while authenticating
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
      />

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Navbar */}
        <Navbar 
          onMenuClick={() => setSidebarOpen(true)}
          isConnected={isConnected}
        />

        {/* Page content */}
        <main className="py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        >
          <div className="absolute inset-0 bg-gray-800 opacity-75"></div>
        </div>
      )}
    </div>
  );
};

export default Layout;
