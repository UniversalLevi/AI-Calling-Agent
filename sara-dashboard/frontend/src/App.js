/**
 * Sara Dashboard - Main App Component
 * React application for Sara AI Calling Bot admin dashboard
 */

import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Context Providers
import { AuthProvider } from './contexts/AuthContext';
import { SocketProvider } from './contexts/SocketContext';

// Components
import Layout from './components/Layout/Layout';
import ProtectedRoute from './components/Auth/ProtectedRoute';

// Pages
import Login from './pages/Auth/Login';
import Dashboard from './pages/Dashboard/Dashboard';
import CallLogs from './pages/Calls/CallLogs';
import LiveCalls from './pages/Calls/LiveCalls';
import Settings from './pages/Settings/Settings';
import Users from './pages/Users/Users';
import Analytics from './pages/Analytics/Analytics';

// Sales Pages
import ProductManager from './pages/Sales/ProductManager';
import ScriptEditor from './pages/Sales/ScriptEditor';

// Payment and WhatsApp Pages
import Payments from './pages/Payments/Payments';
import WhatsAppMessages from './pages/WhatsApp/WhatsAppMessages';

// Styles
import './index.css';

function App() {
  // Apply dark theme to html element
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  return (
    <AuthProvider>
      <SocketProvider>
        <Router future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true
        }}>
          <div className="App dark">
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              
              {/* Protected Routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="calls" element={<CallLogs />} />
                <Route path="live-calls" element={<LiveCalls />} />
                <Route path="analytics" element={<Analytics />} />
                <Route path="payments" element={<Payments />} />
                <Route path="whatsapp" element={<WhatsAppMessages />} />
                <Route path="sales/products" element={<ProductManager />} />
                <Route path="sales/scripts" element={<ScriptEditor />} />
                <Route path="settings" element={<Settings />} />
                <Route path="users" element={<Users />} />
              </Route>
              
              {/* Catch all route */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
            
            {/* Toast notifications */}
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#10B981',
                    secondary: '#fff',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#EF4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          </div>
        </Router>
      </SocketProvider>
    </AuthProvider>
  );
}

export default App;
