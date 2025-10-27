/**
 * Sara Dashboard - Main Entry Point
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Suppress browser extension errors
window.addEventListener('error', (event) => {
  if (event.filename && (
    event.filename.includes('contentScript.js') ||
    event.filename.includes('extension') ||
    event.filename.includes('chrome-extension')
  )) {
    event.preventDefault();
    return false;
  }
});

window.addEventListener('unhandledrejection', (event) => {
  if (event.reason && event.reason.message && (
    event.reason.message.includes('message port closed') ||
    event.reason.message.includes('extension')
  )) {
    event.preventDefault();
    return false;
  }
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
