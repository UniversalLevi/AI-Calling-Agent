/**
 * Settings Page
 */

import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

const Settings = () => {
  const { user } = useAuth();
  const [voiceSettings, setVoiceSettings] = useState({ tts_voice_english: 'nova', tts_voice_hindi: 'shimmer', tts_language_preference: 'auto' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/system/voice-settings');
        const data = await res.json();
        if (data.success) setVoiceSettings(data.data);
      } catch (e) {
        // noop
      }
    })();
  }, []);

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
                OpenAI English Voice
              </label>
              <select
                className="input-field"
                value={voiceSettings.tts_voice_english}
                onChange={(e) => setVoiceSettings({ ...voiceSettings, tts_voice_english: e.target.value })}
              >
                <option value="nova">nova</option>
                <option value="alloy">alloy</option>
                <option value="echo">echo</option>
                <option value="fable">fable</option>
                <option value="onyx">onyx</option>
                <option value="shimmer">shimmer</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                OpenAI Hindi Voice
              </label>
              <select
                className="input-field"
                value={voiceSettings.tts_voice_hindi}
                onChange={(e) => setVoiceSettings({ ...voiceSettings, tts_voice_hindi: e.target.value })}
              >
                <option value="shimmer">shimmer</option>
                <option value="nova">nova</option>
                <option value="alloy">alloy</option>
                <option value="echo">echo</option>
                <option value="fable">fable</option>
                <option value="onyx">onyx</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Language Preference
              </label>
              <select
                className="input-field"
                value={voiceSettings.tts_language_preference}
                onChange={(e) => setVoiceSettings({ ...voiceSettings, tts_language_preference: e.target.value })}
              >
                <option value="auto">Auto</option>
                <option value="en">English</option>
                <option value="hi">Hindi</option>
              </select>
            </div>
            <div>
              <button
                onClick={async () => {
                  setSaving(true);
                  try {
                    await fetch('/api/system/voice-settings', {
                      method: 'PUT',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(voiceSettings)
                    });
                  } catch (e) {}
                  setSaving(false);
                }}
                className="btn-primary"
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Voice Settings'}
              </button>
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

