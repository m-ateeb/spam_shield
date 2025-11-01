/**
 * Spam Shield - Background Service Worker
 * Handles API communication, authentication, and email analysis
 */

// Configuration
const CONFIG = {
  API_BASE_URL: 'http://localhost:8000', // Change to production URL
  FRONTEND_URL: 'http://localhost:5173',
  STORAGE_KEYS: {
    AUTH_TOKEN: 'spam_shield_token',
    USER_DATA: 'spam_shield_user',
    SETTINGS: 'spam_shield_settings',
    CONNECTED_ACCOUNTS: 'spam_shield_accounts'
  }
};

// ============================================
// INSTALLATION & INITIALIZATION
// ============================================
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('🎉 Spam Shield installed!');
    // Open onboarding page
    chrome.tabs.create({ url: `${CONFIG.FRONTEND_URL}` });
    
    // Set default settings
    chrome.storage.local.set({
      [CONFIG.STORAGE_KEYS.SETTINGS]: {
        autoQuarantine: true,
        notificationsEnabled: true,
        scanInRealTime: true,
        strictMode: false
      }
    });
  } else if (details.reason === 'update') {
    console.log('🔄 Spam Shield updated!');
  }
});

// ============================================
// MESSAGE HANDLERS
// ============================================
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📩 Message received:', request.action);

  switch (request.action) {
    case 'SET_AUTH':
      handleSetAuth(request.data, sendResponse);
      return true;

    case 'ANALYZE_EMAIL':
      handleEmailAnalysis(request.data, sendResponse);
      return true; // Keep channel open for async response

    case 'GET_AUTH_STATUS':
      handleGetAuthStatus(sendResponse);
      return true;

    case 'CONNECT_GMAIL':
      handleConnectGmail(sendResponse);
      return true;

    case 'CONNECT_OUTLOOK':
      handleConnectOutlook(sendResponse);
      return true;

    case 'GET_QUARANTINE_LIST':
      handleGetQuarantine(sendResponse);
      return true;

    case 'RELEASE_EMAIL':
      handleReleaseEmail(request.data, sendResponse);
      return true;

    case 'DELETE_EMAIL':
      handleDeleteEmail(request.data, sendResponse);
      return true;

    case 'GET_STATS':
      handleGetStats(sendResponse);
      return true;

    case 'LOGOUT':
      handleLogout(sendResponse);
      return true;

    default:
      sendResponse({ error: 'Unknown action' });
  }
});

// ============================================
// EMAIL ANALYSIS
// ============================================
async function handleEmailAnalysis(emailData, sendResponse) {
  try {
    const token = await getAuthToken();
    if (!token) {
      sendResponse({ error: 'Not authenticated' });
      return;
    }

    // Send email data to backend for analysis
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/extension/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message_id: emailData.messageId,
        subject: emailData.subject,
        from: emailData.from,
        body_html: emailData.bodyHtml,
        headers: emailData.headers,
        provider: emailData.provider
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    
    // Show notification if spam detected
    if (result.verdict !== 'safe' && await isNotificationsEnabled()) {
      showSpamNotification(emailData.subject, result.verdict);
    }

    sendResponse({ success: true, result });
  } catch (error) {
    console.error('❌ Email analysis error:', error);
    sendResponse({ error: error.message });
  }
}

// ============================================
// AUTHENTICATION
// ============================================
async function handleSetAuth(data, sendResponse) {
  try {
    const { token, user } = data;
    await chrome.storage.local.set({
      [CONFIG.STORAGE_KEYS.AUTH_TOKEN]: token,
      [CONFIG.STORAGE_KEYS.USER_DATA]: user
    });
    console.log('✅ Auth set in extension:', user.email);
    sendResponse({ success: true });
  } catch (error) {
    console.error('❌ Failed to set auth:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function handleGetAuthStatus(sendResponse) {
  try {
    const token = await getAuthToken();
    const userData = await chrome.storage.local.get(CONFIG.STORAGE_KEYS.USER_DATA);
    
    console.log('Auth status check:', { 
      hasToken: !!token, 
      user: userData[CONFIG.STORAGE_KEYS.USER_DATA] 
    });
    
    sendResponse({
      authenticated: !!token,
      user: userData[CONFIG.STORAGE_KEYS.USER_DATA] || null
    });
  } catch (error) {
    console.error('Auth status error:', error);
    sendResponse({ authenticated: false, error: error.message });
  }
}

async function handleConnectGmail(sendResponse) {
  try {
    const token = await getAuthToken();
    if (!token) {
      // Open web app for authentication first
      chrome.tabs.create({ url: `${CONFIG.FRONTEND_URL}/login` });
      sendResponse({ error: 'Please login first' });
      return;
    }

    // Trigger OAuth flow
    const oauthUrl = `${CONFIG.API_BASE_URL}/oauth/google/`;
    chrome.tabs.create({ url: oauthUrl }, (tab) => {
      // Listen for OAuth completion
      chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
        if (tabId === tab.id && info.url && info.url.includes('oauth_success=gmail')) {
          chrome.tabs.remove(tabId);
          chrome.tabs.onUpdated.removeListener(listener);
          sendResponse({ success: true, provider: 'gmail' });
        }
      });
    });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

async function handleConnectOutlook(sendResponse) {
  try {
    const token = await getAuthToken();
    if (!token) {
      chrome.tabs.create({ url: `${CONFIG.FRONTEND_URL}/login` });
      sendResponse({ error: 'Please login first' });
      return;
    }

    const oauthUrl = `${CONFIG.API_BASE_URL}/oauth/microsoft/`;
    chrome.tabs.create({ url: oauthUrl }, (tab) => {
      chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
        if (tabId === tab.id && info.url && info.url.includes('oauth_success=outlook')) {
          chrome.tabs.remove(tabId);
          chrome.tabs.onUpdated.removeListener(listener);
          sendResponse({ success: true, provider: 'outlook' });
        }
      });
    });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

async function handleLogout(sendResponse) {
  try {
    await chrome.storage.local.remove([
      CONFIG.STORAGE_KEYS.AUTH_TOKEN,
      CONFIG.STORAGE_KEYS.USER_DATA,
      CONFIG.STORAGE_KEYS.CONNECTED_ACCOUNTS
    ]);
    sendResponse({ success: true });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

// ============================================
// QUARANTINE MANAGEMENT
// ============================================
async function handleGetQuarantine(sendResponse) {
  try {
    const token = await getAuthToken();
    if (!token) {
      sendResponse({ error: 'Not authenticated' });
      return;
    }

    const response = await fetch(`${CONFIG.API_BASE_URL}/api/quarantine/list/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Failed to fetch quarantine');

    const data = await response.json();
    sendResponse({ success: true, quarantined: data.quarantined });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

async function handleReleaseEmail(data, sendResponse) {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/quarantine/release/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ id: data.id })
    });

    if (!response.ok) throw new Error('Failed to release email');
    
    sendResponse({ success: true });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

async function handleDeleteEmail(data, sendResponse) {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/quarantine/delete/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ id: data.id })
    });

    if (!response.ok) throw new Error('Failed to delete email');
    
    sendResponse({ success: true });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

// ============================================
// STATS
// ============================================
async function handleGetStats(sendResponse) {
  try {
    const token = await getAuthToken();
    if (!token) {
      sendResponse({ error: 'Not authenticated' });
      return;
    }

    const accounts = await chrome.storage.local.get(CONFIG.STORAGE_KEYS.CONNECTED_ACCOUNTS);
    const accountList = accounts[CONFIG.STORAGE_KEYS.CONNECTED_ACCOUNTS] || [];
    
    if (accountList.length === 0) {
      sendResponse({ success: true, stats: null });
      return;
    }

    // Get stats for first connected account
    const email = accountList[0].email_address;
    const response = await fetch(
      `${CONFIG.API_BASE_URL}/api/dashboard/summary/?email=${encodeURIComponent(email)}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );

    if (!response.ok) throw new Error('Failed to fetch stats');

    const stats = await response.json();
    sendResponse({ success: true, stats });
  } catch (error) {
    sendResponse({ error: error.message });
  }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================
async function getAuthToken() {
  const result = await chrome.storage.local.get(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
  return result[CONFIG.STORAGE_KEYS.AUTH_TOKEN] || null;
}

async function isNotificationsEnabled() {
  const settings = await chrome.storage.local.get(CONFIG.STORAGE_KEYS.SETTINGS);
  return settings[CONFIG.STORAGE_KEYS.SETTINGS]?.notificationsEnabled ?? true;
}

function showSpamNotification(subject, verdict) {
  const verdictEmoji = {
    'suspicious': '⚠️',
    'phishing': '🚨',
    'spam': '🛡️'
  };

  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'assets/icons/icon128.png',
    title: `${verdictEmoji[verdict] || '🛡️'} Spam Detected!`,
    message: `Email "${subject.substring(0, 50)}..." has been quarantined`,
    priority: 2
  });
}

// ============================================
// EXTERNAL MESSAGE LISTENER (From Website)
// ============================================
chrome.runtime.onMessageExternal.addListener((request, sender, sendResponse) => {
  console.log('📨 External message received!');
  console.log('   From:', sender.url);
  console.log('   Action:', request.action);
  console.log('   Data:', request.data);
  
  if (request.action === 'SET_AUTH') {
    console.log('   Processing SET_AUTH...');
    handleSetAuth(request.data, sendResponse);
    return true;
  }
  
  if (request.action === 'LOGOUT') {
    console.log('   Processing LOGOUT...');
    handleLogout(sendResponse);
    return true;
  }
  
  console.log('   Unknown action, returning error');
  sendResponse({ error: 'Unknown action' });
});

console.log('🛡️ Spam Shield service worker loaded!');

