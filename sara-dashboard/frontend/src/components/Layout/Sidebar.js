/**
 * Sidebar Component
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { user } = useAuth();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: '📊' },
    { name: 'Live Calls', href: '/live-calls', icon: '📞' },
    { name: 'Call Logs', href: '/calls', icon: '📚' },
    { name: 'Payments', href: '/payments', icon: '💳' },
    { name: 'WhatsApp', href: '/whatsapp', icon: '💬' },
    { name: 'Analytics', href: '/analytics', icon: '📈' },
    { name: 'Sales', href: '/sales/products', icon: '🎯', submenu: [
      { name: 'Products', href: '/sales/products', icon: '📦' },
      { name: 'Scripts', href: '/sales/scripts', icon: '📝' }
    ]},
    { name: 'Settings', href: '/settings', icon: '⚙️' },
  ];

  if (user?.role === 'admin') {
    // Admin-only features can be added here in the future
  }

  return (
    <>
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-dark-sidebar transform ${isOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 transition-transform duration-300 ease-in-out`}>
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between h-16 px-4 bg-dark-card border-b border-dark-border">
            <h1 className="text-xl font-bold text-dark-text">Sara Dashboard</h1>
            <button
              onClick={onClose}
              className="lg:hidden text-dark-text-muted hover:text-dark-text hover:brightness-110"
            >
              ✕
            </button>
          </div>

          <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || 
                (item.submenu && item.submenu.some(sub => location.pathname === sub.href));
              
              if (item.submenu) {
                return (
                  <div key={item.name} className="space-y-1">
                    <div className={`flex items-center px-4 py-3 text-sidebar font-medium rounded-md transition-all duration-200 ${
                      isActive
                        ? 'bg-dark-accent text-white border-l-4 border-dark-accent'
                        : 'text-dark-text-muted hover:bg-dark-hover hover:text-white hover:brightness-110'
                    }`}>
                      <span className="mr-3">{item.icon}</span>
                      {item.name}
                    </div>
                    <div className="ml-4 space-y-1">
                      {item.submenu.map((subItem) => {
                        const isSubActive = location.pathname === subItem.href;
                        return (
                          <Link
                            key={subItem.name}
                            to={subItem.href}
                            onClick={onClose}
                            className={`flex items-center px-4 py-2 text-sidebar font-medium rounded-md transition-all duration-200 ${
                              isSubActive
                                ? 'bg-dark-accent text-white border-l-4 border-dark-accent'
                                : 'text-dark-text-muted hover:bg-dark-hover hover:text-white hover:brightness-110'
                            }`}
                          >
                            <span className="mr-3">{subItem.icon}</span>
                            {subItem.name}
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                );
              }
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={onClose}
                  className={`flex items-center px-4 py-3 text-sidebar font-medium rounded-md transition-all duration-200 ${
                    isActive
                      ? 'bg-dark-accent text-white border-l-4 border-dark-accent'
                      : 'text-dark-text-muted hover:bg-dark-hover hover:text-white hover:brightness-110'
                  }`}
                >
                  <span className="mr-3">{item.icon}</span>
                  {item.name}
                </Link>
              );
            })}
          </nav>

          <div className="p-4 border-t border-dark-border">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-dark-text">
                  {user?.firstName} {user?.lastName}
                </p>
                <p className="text-xs text-dark-text-muted">{user?.role}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;


