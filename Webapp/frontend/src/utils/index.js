// Utility functions for the eBay Optimizer React application
// Merged từ Ebay-UI-New/services/Utils.js

// Formatting functions
export const formatCurrency = (amount, currency = 'USD') => {
  if (amount == null || isNaN(amount)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(amount);
};

export const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return dateString;
  return new Intl.DateTimeFormat('vi-VN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(date);
};

export const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return '';
  const date = new Date(dateTimeString);
  if (isNaN(date.getTime())) return dateTimeString;
  return new Intl.DateTimeFormat('vi-VN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

// Status badge helper for MUI
export const getStatusInfo = (status) => {
  const statusMap = {
    'pending': { label: 'Chờ xử lý', color: 'warning' },
    'processing': { label: 'Đang xử lý', color: 'info' },
    'shipped': { label: 'Đã giao', color: 'success' },
    'delivered': { label: 'Hoàn thành', color: 'success' },
    'cancelled': { label: 'Đã hủy', color: 'error' },
    'returned': { label: 'Hoàn trả', color: 'default' },
    'active': { label: 'Hoạt động', color: 'success' },
    'inactive': { label: 'Không hoạt động', color: 'default' },
    'draft': { label: 'Nháp', color: 'warning' },
    'restricted': { label: 'Bị hạn chế', color: 'warning' },
    'suspended': { label: 'Bị đình chỉ', color: 'error' },
    'under_review': { label: 'Đang xem xét', color: 'info' },
    'connected': { label: 'Kết nối', color: 'success' },
    'disconnected': { label: 'Mất kết nối', color: 'error' },
    'syncing': { label: 'Đang đồng bộ', color: 'info' },
    'out-of-stock': { label: 'Hết hàng', color: 'error' },
  };
  
  return statusMap[status] || { label: status, color: 'default' };
};

// Text helpers
export const truncateText = (text, maxLength = 50) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export const capitalizeFirst = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
};

export const slugify = (text) => {
  return text
    .toLowerCase()
    .replace(/[^\w ]+/g, '')
    .replace(/ +/g, '-');
};

// ID generation
export const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

// Debounce function
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// URL helpers
export const parseQueryString = (queryString) => {
  const params = {};
  const searchParams = new URLSearchParams(queryString);
  for (const [key, value] of searchParams) {
    params[key] = value;
  }
  return params;
};

export const buildQueryString = (params) => {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, value);
    }
  }
  return searchParams.toString();
};

// Object helpers
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime());
  if (obj instanceof Array) return obj.map(item => deepClone(item));
  if (obj instanceof Object) {
    const clonedObj = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
};

export const isEmpty = (value) => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

// Array helpers
export const sortBy = (array, key, direction = 'asc') => {
  return [...array].sort((a, b) => {
    let aVal = a[key];
    let bVal = b[key];
    
    if (typeof aVal === 'string') aVal = aVal.toLowerCase();
    if (typeof bVal === 'string') bVal = bVal.toLowerCase();
    
    if (direction === 'asc') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });
};

export const groupBy = (array, key) => {
  return array.reduce((result, item) => {
    const group = item[key];
    if (!result[group]) {
      result[group] = [];
    }
    result[group].push(item);
    return result;
  }, {});
};

// Local storage helpers (React-safe)
export const getFromStorage = (key, defaultValue = null) => {
  if (typeof window === 'undefined') return defaultValue;
  
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error('Error parsing localStorage item:', error);
    return defaultValue;
  }
};

export const setToStorage = (key, value) => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error('Error setting localStorage item:', error);
  }
};

export const removeFromStorage = (key) => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Error removing localStorage item:', error);
  }
};

// Number helpers
export const formatNumber = (number, decimals = 2) => {
  if (number == null || isNaN(number)) return '0';
  return number.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const formatPercentage = (value, decimals = 1) => {
  if (value == null || isNaN(value)) return '0%';
  return `${value.toFixed(decimals)}%`;
};

export const calculatePercentage = (part, total) => {
  if (!total || total === 0) return 0;
  return (part / total) * 100;
};

// File helpers
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const getFileExtension = (filename) => {
  if (!filename) return '';
  return filename.split('.').pop().toLowerCase();
};

// Validation helpers
export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const isValidPhone = (phone) => {
  const phoneRegex = /^\+?[\d\s\-()]{10,}$/;
  return phoneRegex.test(phone);
};

export const isValidUrl = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

// Color helpers
export const getRandomColor = () => {
  const colors = [
    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
    '#9966FF', '#FF9F40', '#FF6384', '#4BC0C0'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
};

export const hexToRgba = (hex, alpha = 1) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return hex;
  
  const r = parseInt(result[1], 16);
  const g = parseInt(result[2], 16);
  const b = parseInt(result[3], 16);
  
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

// Export all as default object too (for easier import)
const utils = {
  formatCurrency,
  formatDate,
  formatDateTime,
  getStatusInfo,
  truncateText,
  capitalizeFirst,
  slugify,
  generateId,
  debounce,
  parseQueryString,
  buildQueryString,
  deepClone,
  isEmpty,
  sortBy,
  groupBy,
  getFromStorage,
  setToStorage,
  removeFromStorage,
  formatNumber,
  formatPercentage,
  calculatePercentage,
  formatFileSize,
  getFileExtension,
  isValidEmail,
  isValidPhone,
  isValidUrl,
  getRandomColor,
  hexToRgba,
};

export default utils;