/**
 * Navbar Component
 */

import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

const Navbar = ({ onMenuClick, isConnected }) => {
  const { user, logout } = useAuth();

  return (
    <div className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <button
              onClick={onMenuClick}
              className="lg:hidden text-gray-500 hover:text-gray-700"
            >
              <span className="text-2xl">☰</span>
            </button>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-700">
                {user?.username}
              </span>
              <button
                onClick={logout}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Navbar;


