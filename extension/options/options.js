/**
 * Spam Shield - Options/Settings Script
 */

const STORAGE_KEY = 'spam_shield_settings';

// Default settings
const DEFAULT_SETTINGS = {
  autoQuarantine: true,
  scanInRealTime: true,
  strictMode: false,
  notificationsEnabled: true,
  notifyOnQuarantine: true,
  notifyOnPhishing: true,
  apiBaseUrl: 'http://localhost:8000',
  frontendUrl: 'http://localhost:5173'
};

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  attachEventListeners();
});

function attachEventListeners() {
  // Save button
  document.getElementById('saveBtn').addEventListener('click', saveSettings);

  // Setting changes (auto-save on toggle)
  const toggles = document.querySelectorAll('input[type="checkbox"]');
  toggles.forEach(toggle => {
    toggle.addEventListener('change', () => {
      showStatusMessage('Settings will be saved when you click "Save Changes"', 'info');
    });
  });

  // Text inputs
  const textInputs = document.querySelectorAll('.text-input');
  textInputs.forEach(input => {
    input.addEventListener('input', () => {
      showStatusMessage('Settings will be saved when you click "Save Changes"', 'info');
    });
  });

  // Action buttons
  document.getElementById('clearCacheBtn').addEventListener('click', handleClearCache);
  document.getElementById('exportDataBtn').addEventListener('click', handleExportData);

  // Links
  document.getElementById('helpLink').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'http://localhost:5173/features' });
  });
  document.getElementById('privacyLink').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'http://localhost:5173/privacy' });
  });
  document.getElementById('termsLink').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'http://localhost:5173/terms' });
  });
}

// ============================================
// LOAD SETTINGS
// ============================================
async function loadSettings() {
  try {
    const result = await chrome.storage.local.get(STORAGE_KEY);
    const settings = result[STORAGE_KEY] || DEFAULT_SETTINGS;

    // Apply settings to UI
    document.getElementById('autoQuarantine').checked = settings.autoQuarantine;
    document.getElementById('scanInRealTime').checked = settings.scanInRealTime;
    document.getElementById('strictMode').checked = settings.strictMode;
    document.getElementById('notificationsEnabled').checked = settings.notificationsEnabled;
    document.getElementById('notifyOnQuarantine').checked = settings.notifyOnQuarantine;
    document.getElementById('notifyOnPhishing').checked = settings.notifyOnPhishing;
    document.getElementById('apiBaseUrl').value = settings.apiBaseUrl;
    document.getElementById('frontendUrl').value = settings.frontendUrl;

    console.log('✅ Settings loaded');
  } catch (error) {
    console.error('Error loading settings:', error);
    showStatusMessage('Failed to load settings', 'error');
  }
}

// ============================================
// SAVE SETTINGS
// ============================================
async function saveSettings() {
  try {
    const settings = {
      autoQuarantine: document.getElementById('autoQuarantine').checked,
      scanInRealTime: document.getElementById('scanInRealTime').checked,
      strictMode: document.getElementById('strictMode').checked,
      notificationsEnabled: document.getElementById('notificationsEnabled').checked,
      notifyOnQuarantine: document.getElementById('notifyOnQuarantine').checked,
      notifyOnPhishing: document.getElementById('notifyOnPhishing').checked,
      apiBaseUrl: document.getElementById('apiBaseUrl').value.trim(),
      frontendUrl: document.getElementById('frontendUrl').value.trim()
    };

    // Validate URLs
    if (!isValidUrl(settings.apiBaseUrl)) {
      showStatusMessage('Invalid API URL', 'error');
      return;
    }
    if (!isValidUrl(settings.frontendUrl)) {
      showStatusMessage('Invalid Frontend URL', 'error');
      return;
    }

    // Save to storage
    await chrome.storage.local.set({ [STORAGE_KEY]: settings });

    // Update background worker config
    await updateBackgroundConfig(settings);

    showStatusMessage('✅ Settings saved successfully!', 'success');
    console.log('✅ Settings saved:', settings);

  } catch (error) {
    console.error('Error saving settings:', error);
    showStatusMessage('❌ Failed to save settings', 'error');
  }
}

// ============================================
// ACTIONS
// ============================================
async function handleClearCache() {
  if (!confirm('This will clear all cached email analysis results. Continue?')) {
    return;
  }

  try {
    // Clear specific cache items
    await chrome.storage.local.remove(['email_analysis_cache']);
    showStatusMessage('✅ Cache cleared successfully', 'success');
  } catch (error) {
    showStatusMessage('❌ Failed to clear cache', 'error');
  }
}

async function handleExportData() {
  try {
    // Get all stored data
    const allData = await chrome.storage.local.get(null);
    
    // Remove sensitive tokens
    const exportData = { ...allData };
    delete exportData.spam_shield_token;
    
    // Create downloadable file
    const dataStr = JSON.stringify(exportData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `spam-shield-data-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showStatusMessage('✅ Data exported successfully', 'success');
  } catch (error) {
    console.error('Error exporting data:', error);
    showStatusMessage('❌ Failed to export data', 'error');
  }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================
function isValidUrl(string) {
  try {
    new URL(string);
    return true;
  } catch (_) {
    return false;
  }
}

function showStatusMessage(message, type = 'info') {
  const statusEl = document.getElementById('statusMessage');
  statusEl.textContent = message;
  statusEl.className = `status-message ${type} show`;

  // Auto-hide after 3 seconds
  setTimeout(() => {
    statusEl.classList.remove('show');
  }, 3000);
}

async function updateBackgroundConfig(settings) {
  // Send message to background worker to update config
  try {
    await chrome.runtime.sendMessage({
      action: 'UPDATE_CONFIG',
      data: {
        apiBaseUrl: settings.apiBaseUrl,
        frontendUrl: settings.frontendUrl
      }
    });
  } catch (error) {
    console.error('Failed to update background config:', error);
  }
}

// ============================================
// KEYBOARD SHORTCUTS
// ============================================
document.addEventListener('keydown', (e) => {
  // Ctrl+S or Cmd+S to save
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    saveSettings();
  }
});

