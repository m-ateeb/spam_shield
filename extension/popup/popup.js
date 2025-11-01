/**
 * Spam Shield - Popup Script
 * Handles extension popup UI and interactions
 */

const CONFIG = {
  FRONTEND_URL: 'http://localhost:5173'
};

// DOM Elements
let elements = {};

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', async () => {
  initializeElements();
  attachEventListeners();
  await loadPopupData();
});

function initializeElements() {
  elements = {
    // Views
    loadingView: document.getElementById('loadingView'),
    notAuthView: document.getElementById('notAuthView'),
    authView: document.getElementById('authView'),
    
    // Stats
    totalEmails: document.getElementById('totalEmails'),
    spamBlocked: document.getElementById('spamBlocked'),
    quarantined: document.getElementById('quarantined'),
    
    // Accounts
    accountsList: document.getElementById('accountsList'),
    
    // Buttons
    loginBtn: document.getElementById('loginBtn'),
    logoutBtn: document.getElementById('logoutBtn'),
    connectGmailBtn: document.getElementById('connectGmailBtn'),
    connectOutlookBtn: document.getElementById('connectOutlookBtn'),
    viewQuarantineBtn: document.getElementById('viewQuarantineBtn'),
    openDashboardBtn: document.getElementById('openDashboardBtn'),
    settingsBtn: document.getElementById('settingsBtn')
  };
}

function attachEventListeners() {
  elements.loginBtn?.addEventListener('click', handleLogin);
  elements.logoutBtn?.addEventListener('click', handleLogout);
  elements.connectGmailBtn?.addEventListener('click', handleConnectGmail);
  elements.connectOutlookBtn?.addEventListener('click', handleConnectOutlook);
  elements.viewQuarantineBtn?.addEventListener('click', handleViewQuarantine);
  elements.openDashboardBtn?.addEventListener('click', handleOpenDashboard);
  elements.settingsBtn?.addEventListener('click', handleOpenSettings);
}

// ============================================
// DATA LOADING
// ============================================
async function loadPopupData() {
  showLoading();

  try {
    // Check auth status
    const authResponse = await chrome.runtime.sendMessage({ action: 'GET_AUTH_STATUS' });
    
    if (!authResponse.authenticated) {
      showNotAuthView();
      return;
    }

    // Load stats
    await loadStats();
    
    // Load connected accounts
    await loadAccounts();
    
    showAuthView();
  } catch (error) {
    console.error('Error loading popup data:', error);
    showError('Failed to load data');
  }
}

async function loadStats() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'GET_STATS' });
    
    if (response.error) {
      console.error('Stats error:', response.error);
      return;
    }

    if (response.stats) {
      elements.totalEmails.textContent = response.stats.total_emails || 0;
      elements.spamBlocked.textContent = response.stats.suspicious_emails || 0;
      elements.quarantined.textContent = response.stats.quarantined_emails || 0;
    }
  } catch (error) {
    console.error('Error loading stats:', error);
  }
}

async function loadAccounts() {
  try {
    // Get from local storage (synced from backend)
    const result = await chrome.storage.local.get('spam_shield_accounts');
    const accounts = result.spam_shield_accounts || [];

    if (accounts.length === 0) {
      elements.accountsList.innerHTML = `
        <div class="empty-state">
          <p>No email accounts connected</p>
          <p class="hint">Connect Gmail or Outlook to start</p>
        </div>
      `;
      return;
    }

    // Display accounts
    elements.accountsList.innerHTML = accounts.map(account => `
      <div class="account-item">
        <div class="account-icon">${account.provider === 'gmail' ? '📧' : '📮'}</div>
        <div class="account-info">
          <div class="account-email">${account.email_address}</div>
          <div class="account-status ${account.inbox_sync_status}">
            ${account.inbox_sync_status === 'connected' ? '✓ Connected' : '⚠️ Disconnected'}
          </div>
        </div>
      </div>
    `).join('');
  } catch (error) {
    console.error('Error loading accounts:', error);
    elements.accountsList.innerHTML = '<p class="error">Failed to load accounts</p>';
  }
}

// ============================================
// UI STATE MANAGEMENT
// ============================================
function showLoading() {
  elements.loadingView.style.display = 'flex';
  elements.notAuthView.style.display = 'none';
  elements.authView.style.display = 'none';
}

function showNotAuthView() {
  elements.loadingView.style.display = 'none';
  elements.notAuthView.style.display = 'block';
  elements.authView.style.display = 'none';
}

function showAuthView() {
  elements.loadingView.style.display = 'none';
  elements.notAuthView.style.display = 'none';
  elements.authView.style.display = 'block';
}

function showError(message) {
  // Simple error display - can be enhanced
  console.error(message);
  alert(message);
}

// ============================================
// EVENT HANDLERS
// ============================================
function handleLogin() {
  chrome.tabs.create({ url: `${CONFIG.FRONTEND_URL}/login` });
  window.close();
}

async function handleLogout() {
  if (!confirm('Are you sure you want to logout?')) {
    return;
  }

  try {
    await chrome.runtime.sendMessage({ action: 'LOGOUT' });
    showNotAuthView();
  } catch (error) {
    showError('Logout failed');
  }
}

async function handleConnectGmail() {
  showButtonLoading(elements.connectGmailBtn);
  
  try {
    const response = await chrome.runtime.sendMessage({ action: 'CONNECT_GMAIL' });
    
    if (response.error) {
      showError(response.error);
    } else {
      // OAuth window will open - close popup
      window.close();
    }
  } catch (error) {
    showError('Failed to connect Gmail');
  } finally {
    resetButton(elements.connectGmailBtn, '<span class="btn-icon">📧</span> Connect Gmail');
  }
}

async function handleConnectOutlook() {
  showButtonLoading(elements.connectOutlookBtn);
  
  try {
    const response = await chrome.runtime.sendMessage({ action: 'CONNECT_OUTLOOK' });
    
    if (response.error) {
      showError(response.error);
    } else {
      window.close();
    }
  } catch (error) {
    showError('Failed to connect Outlook');
  } finally {
    resetButton(elements.connectOutlookBtn, '<span class="btn-icon">📮</span> Connect Outlook');
  }
}

async function handleViewQuarantine() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'GET_QUARANTINE_LIST' });
    
    if (response.error) {
      showError(response.error);
      return;
    }

    // Open quarantine view in dashboard
    chrome.tabs.create({ url: `${CONFIG.FRONTEND_URL}/user#quarantine` });
    window.close();
  } catch (error) {
    showError('Failed to load quarantine');
  }
}

function handleOpenDashboard() {
  chrome.tabs.create({ url: `${CONFIG.FRONTEND_URL}/user` });
  window.close();
}

function handleOpenSettings() {
  chrome.runtime.openOptionsPage();
}

// ============================================
// UTILITY FUNCTIONS
// ============================================
function showButtonLoading(button) {
  button.disabled = true;
  button.innerHTML = '<span class="btn-spinner">⏳</span> Loading...';
}

function resetButton(button, originalHTML) {
  button.disabled = false;
  button.innerHTML = originalHTML;
}

// ============================================
// AUTO REFRESH
// ============================================
// Refresh stats every 30 seconds if popup is open
setInterval(async () => {
  const authResponse = await chrome.runtime.sendMessage({ action: 'GET_AUTH_STATUS' });
  if (authResponse.authenticated) {
    await loadStats();
  }
}, 30000);

