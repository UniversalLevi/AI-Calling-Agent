/**
 * Settings Page
 */

import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

const Settings = () => {
  const { user } = useAuth();

  return (
    <div className="fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="mt-2 text-sm text-gray-300">
          Manage system configuration and preferences
        </p>
      </div>

      {/* System Settings */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* General Settings */}
        <div className="card">
          <h2 className="text-xl font-semibold text-white mb-4">
            General Settings
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                System Language
              </label>
              <select className="input-field">
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="mixed">Hinglish (Mixed)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Voice Type
              </label>
              <select className="input-field">
                <option value="openai">OpenAI TTS</option>
                <option value="twilio">Twilio Voice</option>
              </select>
            </div>
          </div>
        </div>

        {/* Call Settings */}
        <div className="card">
          <h2 className="text-xl font-semibold text-white mb-4">
            Call Settings
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Max Concurrent Calls
              </label>
              <input
                type="number"
                className="input-field"
                defaultValue="10"
                min="1"
                max="100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Call Timeout (seconds)
              </label>
              <input
                type="number"
                className="input-field"
                defaultValue="300"
                min="60"
                max="1800"
              />
            </div>
          </div>
        </div>

        {/* User Profile */}
        <div className="card">
          <h2 className="text-xl font-semibold text-white mb-4">
            User Profile
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Username
              </label>
              <input
                type="text"
                className="input-field"
                value={user?.username || ''}
                disabled
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <input
                type="email"
                className="input-field"
                value={user?.email || ''}
                disabled
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Role
              </label>
              <input
                type="text"
                className="input-field"
                value={user?.role || ''}
                disabled
              />
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="card">
          <h2 className="text-xl font-semibold text-white mb-4">
            Notifications
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">
                Email Notifications
              </label>
              <input
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                defaultChecked
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">
                Dashboard Notifications
              </label>
              <input
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                defaultChecked
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">
                Call Alerts
              </label>
              <input
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                defaultChecked
              />
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="mt-6">
        <button className="btn-primary">
          Save Settings
        </button>
      </div>
    </div>
  );
};

export default Settings;

