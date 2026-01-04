/**
 * API Configuration
 * Dynamically determines API URL based on environment
 */

// Determine API URL based on environment
const getApiUrl = () => {
  // In production build, use environment variable
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // If running on production domain, use same domain
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return `${window.location.protocol}//${window.location.hostname}/api`;
  }
  
  // Development fallback
  return 'http://localhost:5016/api';
};

// Determine Socket URL based on environment
const getSocketUrl = () => {
  // In production build, use environment variable
  if (process.env.REACT_APP_SOCKET_URL) {
    return process.env.REACT_APP_SOCKET_URL;
  }
  
  // If running on production domain, use same domain
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return `${window.location.protocol}//${window.location.hostname}`;
  }
  
  // Development fallback
  return 'http://localhost:5016';
};

export const API_URL = getApiUrl();
export const SOCKET_URL = getSocketUrl();

