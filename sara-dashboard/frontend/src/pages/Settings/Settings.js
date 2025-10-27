/**
 * Settings Page
 */

import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';

const Settings = () => {
  const { user } = useAuth();
  const [voiceSettings, setVoiceSettings] = useState({ 
    tts_voice_english: 'nova', 
    tts_voice_hindi: 'shimmer', 
    tts_language_preference: 'auto',
    tts_provider: 'openai',
    tts_speed: 0.9,
    humanized_mode: true,
    filler_frequency: 0.15,
    hindi_bias_threshold: 0.8,
    emotion_detection_mode: 'hybrid',
    enable_spoken_tone_converter: true,
    enable_micro_sentences: true,
    enable_semantic_pacing: true
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        // Load voice settings
        const voiceRes = await axios.get('/api/system/voice-settings');
        if (voiceRes.data.success) {
          setVoiceSettings(prev => ({ ...prev, ...voiceRes.data.data }));
        }
        
        // Load humanization settings
        const humanizationRes = await axios.get('/api/system/humanization-settings');
        if (humanizationRes.data.success) {
          setVoiceSettings(prev => ({ ...prev, ...humanizationRes.data.data }));
        }
      } catch (e) {
        console.error('Error loading settings:', e);
      }
    })();
  }, []);

  return (
    <div className="fade-in">
      <div className="mb-8">
        <h1 className="text-heading-lg font-bold text-dark-text">Settings</h1>
        <p className="mt-2 text-sm text-dark-text-muted">
          Manage system configuration and preferences
        </p>
      </div>

      {/* System Settings */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* General Settings */}
        <div className="card">
          <h2 className="text-xl font-semibold text-dark-text mb-4">
            General Settings
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-text-muted mb-2">
                System Language
              </label>
              <select className="input-field">
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="mixed">Hinglish (Mixed)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text-muted mb-2">
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
              <label className="block text-sm font-medium text-dark-text-muted mb-2">
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
              <label className="block text-sm font-medium text-dark-text-muted mb-2">
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
              <label className="block text-sm font-medium text-dark-text-muted mb-2">
                TTS Speed
              </label>
              <input
                type="range"
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                min="0.5"
                max="1.5"
                step="0.1"
                value={voiceSettings.tts_speed}
                onChange={(e) => setVoiceSettings({ ...voiceSettings, tts_speed: parseFloat(e.target.value) })}
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0.5x</span>
                <span className="font-medium">{voiceSettings.tts_speed}x</span>
                <span>1.5x</span>
              </div>
            </div>
            <div>
              <button
                onClick={async () => {
                  setSaving(true);
                  try {
                    await axios.put('/api/system/voice-settings', voiceSettings);
                    alert('Voice settings saved successfully!');
                  } catch (e) {
                    console.error('Error saving voice settings:', e);
                    alert('Error saving voice settings');
                  }
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

        {/* Humanization Settings */}
        <div className="card">
          <h2 className="text-xl font-semibold text-dark-text mb-4">
            Humanization Settings
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-dark-text-muted">
                Humanized Mode
              </label>
              <input
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                checked={voiceSettings.humanized_mode}
                onChange={(e) => setVoiceSettings({ ...voiceSettings, humanized_mode: e.target.checked })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text-muted mb-2">
                Filler Word Frequency
              </label>
              <input
                type="range"
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                min="0"
                max="0.5"
                step="0.05"
                value={voiceSettings.filler_frequency}
                onChange={(e) => setVoiceSettings({ ...voiceSettings, filler_frequency: parseFloat(e.target.value) })}
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0%</span>
                <span className="font-medium">{Math.round(voiceSettings.filler_frequency * 100)}%</span>
                <span>50%</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text-muted mb-2">
                Hindi Bias Threshold
              </label>
              <input
                type="range"
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                min="0"
                max="1"
                step="0.1"
                value={voiceSettings.hindi_bias_threshold}
                onChange={(e) => setVoiceSettings({ ...voiceSettings, hindi_bias_threshold: parseFloat(e.target.value) })}
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0%</span>
                <span className="font-medium">{Math.round(voiceSettings.hindi_bias_threshold * 100)}%</span>
                <span>100%</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text-muted mb-2">
                Emotion Detection Mode
              </label>
              <select
                className="input-field"
                value={voiceSettings.emotion_detection_mode}
                onChange={(e) => setVoiceSettings({ ...voiceSettings, emotion_detection_mode: e.target.value })}
              >
                <option value="none">None</option>
                <option value="keyword">Keyword Only</option>
                <option value="hybrid">Hybrid (Keyword + GPT)</option>
                <option value="gpt">GPT Only</option>
              </select>
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-dark-text-muted">
                Spoken Tone Converter
              </label>
              <input
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                checked={voiceSettings.enable_spoken_tone_converter}
                onChange={(e) => setVoiceSettings({ ...voiceSettings, enable_spoken_tone_converter: e.target.checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-dark-text-muted">
                Micro Sentences
              </label>
              <input
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                checked={voiceSettings.enable_micro_sentences}
                onChange={(e) => setVoiceSettings({ ...voiceSettings, enable_micro_sentences: e.target.checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-dark-text-muted">
                Semantic Pacing
              </label>
              <input
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                checked={voiceSettings.enable_semantic_pacing}
                onChange={(e) => setVoiceSettings({ ...voiceSettings, enable_semantic_pacing: e.target.checked })}
              />
            </div>
            <div>
              <button
                onClick={async () => {
                  setSaving(true);
                  try {
                    await axios.put('/api/system/humanization-settings', voiceSettings);
                    alert('Humanization settings saved successfully!');
                  } catch (e) {
                    console.error('Error saving humanization settings:', e);
                    alert('Error saving humanization settings');
                  }
                  setSaving(false);
                }}
                className="btn-primary"
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Humanization Settings'}
              </button>
            </div>
          </div>
        </div>

        {/* User Profile */}
        <div className="card">
          <h2 className="text-xl font-semibold text-dark-text mb-4">
            User Profile
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-text-muted mb-2">
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
              <label className="block text-sm font-medium text-dark-text-muted mb-2">
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
              <label className="block text-sm font-medium text-dark-text-muted mb-2">
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

