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
    { name: 'Analytics', href: '/analytics', icon: '📈' },
    { name: 'Sales', href: '/sales/products', icon: '🎯', submenu: [
      { name: 'Products', href: '/sales/products', icon: '📦' },
      { name: 'Scripts', href: '/sales/scripts', icon: '📝' }
    ]},
    { name: 'Settings', href: '/settings', icon: '⚙️' },
  ];

  if (user?.role === 'admin') {
    navigation.push({ name: 'Users', href: '/users', icon: '👥' });
  }

  return (
    <>
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 transform ${isOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 transition-transform duration-300 ease-in-out`}>
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between h-16 px-4 bg-gray-800">
            <h1 className="text-xl font-bold text-white">Sara Dashboard</h1>
            <button
              onClick={onClose}
              className="lg:hidden text-gray-400 hover:text-white"
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
                    <div className={`flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors ${
                      isActive
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white'
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
                            className={`flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                              isSubActive
                                ? 'bg-gray-700 text-white'
                                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
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
                  className={`flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  <span className="mr-3">{item.icon}</span>
                  {item.name}
                </Link>
              );
            })}
          </nav>

          <div className="p-4 border-t border-gray-800">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-white">
                  {user?.firstName} {user?.lastName}
                </p>
                <p className="text-xs text-gray-400">{user?.role}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;


