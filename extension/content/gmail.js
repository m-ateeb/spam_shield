/**
 * Spam Shield - Gmail Content Script
 * Monitors Gmail interface and adds spam indicators
 */

console.log('🛡️ Spam Shield Gmail extension loaded!');

// Configuration
const GMAIL_SELECTORS = {
  EMAIL_VIEW: 'div[role="main"]',
  EMAIL_SUBJECT: 'h2.hP',
  EMAIL_SENDER: 'span.gD',
  EMAIL_BODY: 'div.a3s',
  EMAIL_TOOLBAR: 'div.iH',
  EMAIL_ROW: 'tr.zA'
};

let currentEmailId = null;
let analysisCache = new Map();
let authPopupShown = false; // Prevent infinite auth popups

// ============================================
// INITIALIZATION
// ============================================
function init() {
  console.log('🚀 Initializing Gmail spam detection...');
  console.log('✅ Spam Shield extension is active on Gmail');
  
  // Monitor for email view changes
  observeEmailView();
  
  // Add spam indicators to inbox list
  observeInboxList();
  
  // Log initialization success
  console.log('✅ Gmail spam detection initialized successfully');
}

// ============================================
// EMAIL VIEW MONITORING
// ============================================
function observeEmailView() {
  let lastUrl = window.location.href;
  let debounceTimer = null;
  
  const observer = new MutationObserver((mutations) => {
    // Only check if we're actually on an email view page (not inbox list)
    const currentUrl = window.location.href;
    const isEmailView = currentUrl.includes('/mail/u/') && (currentUrl.includes('#inbox/') || currentUrl.includes('#search/'));
    
    // Skip if URL hasn't changed (just DOM mutations from other sources)
    if (currentUrl === lastUrl && !isEmailView) {
      return;
    }
    
    // Check if we're viewing an actual email (has subject and sender)
    const emailSubject = document.querySelector(GMAIL_SELECTORS.EMAIL_SUBJECT);
    const emailSender = document.querySelector(GMAIL_SELECTORS.EMAIL_SENDER);
    const emailBody = document.querySelector(GMAIL_SELECTORS.EMAIL_BODY);
    
    // Only proceed if we have all email elements (actual email view, not inbox list)
    if (!emailSubject || !emailSender || !emailBody) {
      lastUrl = currentUrl;
      return;
    }
    
    // Debounce to avoid multiple triggers on rapid navigation
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    
    debounceTimer = setTimeout(() => {
      lastUrl = currentUrl;
      handleEmailOpened();
    }, 500); // Wait 500ms after navigation stops
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: false // Don't trigger on attribute changes
  });
  
  // Also listen for URL changes (Gmail uses pushState for navigation)
  const originalPushState = history.pushState;
  history.pushState = function(...args) {
    originalPushState.apply(history, args);
    // Reset lastUrl to trigger check on next mutation
    lastUrl = '';
  };
}

async function handleEmailOpened() {
  try {
    const emailData = extractEmailData();
    if (!emailData || currentEmailId === emailData.messageId) {
      return; // Same email, skip
    }

    currentEmailId = emailData.messageId;
    console.log('📧 Email opened:', emailData.subject);

    // Check cache first
    if (analysisCache.has(emailData.messageId)) {
      const cachedResult = analysisCache.get(emailData.messageId);
      displaySpamIndicator(cachedResult);
      return;
    }

    // Show loading indicator
    showLoadingIndicator();

    // Send to background for analysis
    let response;
    try {
      response = await chrome.runtime.sendMessage({
        action: 'ANALYZE_EMAIL',
        data: emailData
      });
    } catch (error) {
      // Handle extension context invalidation
      if (error.message && error.message.includes('Extension context invalidated')) {
        console.log('🔄 Extension was reloaded. Please refresh this page (F5)');
        showExtensionReloadPopup();
        removeLoadingIndicator();
        return;
      }
      throw error;
    }

    if (!response) {
      console.error('❌ No response from extension');
      removeLoadingIndicator();
      return;
    }

    if (response.error) {
      console.error('❌ Analysis error:', response.error);
      removeLoadingIndicator();
      
      // Show user-friendly error popup
      if (response.error === 'Not authenticated') {
        showAuthRequiredPopup();
      } else if (response.error.includes('404')) {
        console.error('❌ API endpoint not found. Please restart the Django server.');
      }
      return;
    }

    // Cache result
    analysisCache.set(emailData.messageId, response.result);

    // Display result
    removeLoadingIndicator();
    displaySpamIndicator(response.result);

  } catch (error) {
    removeLoadingIndicator();
    
    // Handle extension context invalidation (extension was reloaded)
    if (error.message && (error.message.includes('Extension context invalidated') || 
        error.message.includes('message port closed') ||
        error.message.includes('Receiving end does not exist'))) {
      console.log('🔄 Extension was reloaded. Please refresh this page (F5) to re-enable spam protection.');
      showExtensionReloadPopup();
      return;
    }
    
    console.error('❌ Error handling email:', error);
    // Don't show error popup for context invalidation - user will see reload message
  }
}

// ============================================
// EMAIL DATA EXTRACTION
// ============================================
function extractEmailData() {
  try {
    // Get message ID from URL
    const urlParams = new URLSearchParams(window.location.hash.substring(1));
    const messageId = urlParams.get('message_id') || extractMessageIdFromDOM();

    const subject = document.querySelector(GMAIL_SELECTORS.EMAIL_SUBJECT)?.textContent?.trim() || '';
    const senderElement = document.querySelector(GMAIL_SELECTORS.EMAIL_SENDER);
    const from = senderElement?.getAttribute('email') || senderElement?.textContent?.trim() || '';
    
    const bodyElement = document.querySelector(GMAIL_SELECTORS.EMAIL_BODY);
    const bodyHtml = bodyElement?.innerHTML || '';

    // Extract headers (limited access in Gmail)
    const headers = {
      subject: subject,
      from: from,
      to: extractRecipient(),
      date: extractDate()
    };

    return {
      messageId: messageId || generateTempId(),
      subject,
      from,
      bodyHtml,
      headers,
      provider: 'gmail'
    };
  } catch (error) {
    console.error('❌ Error extracting email data:', error);
    return null;
  }
}

function extractMessageIdFromDOM() {
  // Try to extract from data attributes
  const emailContainer = document.querySelector('[data-message-id]');
  return emailContainer?.getAttribute('data-message-id') || null;
}

function extractRecipient() {
  const toElement = document.querySelector('span.g2');
  return toElement?.textContent?.trim() || '';
}

function extractDate() {
  const dateElement = document.querySelector('span.g3');
  return dateElement?.getAttribute('title') || dateElement?.textContent?.trim() || '';
}

function generateTempId() {
  return `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ============================================
// SPAM INDICATOR UI
// ============================================
function displaySpamIndicator(result) {
  // Remove existing indicator
  const existingIndicator = document.getElementById('spam-shield-indicator');
  if (existingIndicator) {
    existingIndicator.remove();
  }

  const toolbar = document.querySelector(GMAIL_SELECTORS.EMAIL_TOOLBAR);
  if (!toolbar) return;

  const indicator = createIndicatorElement(result);
  toolbar.insertBefore(indicator, toolbar.firstChild);
  
  // Only show prominent popup notification for threats (phishing/suspicious), not for safe emails
  const { verdict, action } = result;
  if (verdict === 'phishing' || verdict === 'suspicious' || action === 'delete' || action === 'quarantine') {
    showEmailAnalysisPopup(result);
  }
}

function createIndicatorElement(result) {
  const container = document.createElement('div');
  container.id = 'spam-shield-indicator';
  container.className = 'spam-shield-indicator';

  const { verdict, action, reason } = result;

  let status = 'safe';
  let icon = '✅';
  let text = 'Safe';
  let color = '#10b981';

  if (verdict === 'phishing' || action === 'delete') {
    status = 'danger';
    icon = '🚨';
    text = 'Phishing Detected';
    color = '#ef4444';
  } else if (verdict === 'suspicious' || action === 'quarantine') {
    status = 'warning';
    icon = '⚠️';
    text = 'Suspicious';
    color = '#f59e0b';
  }

  container.innerHTML = `
    <div class="spam-shield-badge ${status}" style="background-color: ${color};">
      <span class="spam-shield-icon">${icon}</span>
      <span class="spam-shield-text">${text}</span>
      <span class="spam-shield-info" title="${reason || 'Email passed all security checks'}">ℹ️</span>
    </div>
  `;

  // Add click handler for more details
  container.querySelector('.spam-shield-info').addEventListener('click', (e) => {
    e.stopPropagation();
    showDetailsPopup(result);
  });

  return container;
}

function showLoadingIndicator() {
  const toolbar = document.querySelector(GMAIL_SELECTORS.EMAIL_TOOLBAR);
  if (!toolbar) return;

  const loader = document.createElement('div');
  loader.id = 'spam-shield-loader';
  loader.className = 'spam-shield-indicator';
  loader.innerHTML = `
    <div class="spam-shield-badge loading">
      <span class="spam-shield-spinner">⏳</span>
      <span class="spam-shield-text">Analyzing...</span>
    </div>
  `;
  toolbar.insertBefore(loader, toolbar.firstChild);
}

function removeLoadingIndicator() {
  const loader = document.getElementById('spam-shield-loader');
  if (loader) loader.remove();
}

function showDetailsPopup(result) {
  const popup = document.createElement('div');
  popup.className = 'spam-shield-details-popup';
  popup.innerHTML = `
    <div class="spam-shield-details-content">
      <h3>🛡️ Spam Shield Analysis</h3>
      <div class="detail-row">
        <strong>Verdict:</strong> ${result.verdict || 'Unknown'}
      </div>
      <div class="detail-row">
        <strong>Action:</strong> ${result.action || 'None'}
      </div>
      <div class="detail-row">
        <strong>Reason:</strong> ${result.reason || 'N/A'}
      </div>
      ${result.auth_score !== undefined ? `
        <div class="detail-row">
          <strong>Auth Score:</strong> ${result.auth_score}/100
        </div>
      ` : ''}
      <button class="spam-shield-close-btn">Close</button>
    </div>
  `;

  document.body.appendChild(popup);

  popup.querySelector('.spam-shield-close-btn').addEventListener('click', () => {
    popup.remove();
  });

  // Close on outside click
  popup.addEventListener('click', (e) => {
    if (e.target === popup) {
      popup.remove();
    }
  });
}

function showEmailAnalysisPopup(result) {
  // Remove existing popup if any
  const existingPopup = document.getElementById('spam-shield-email-popup');
  if (existingPopup) {
    existingPopup.remove();
  }

  const { verdict, action, reason } = result;

  let status = 'safe';
  let icon = '✅';
  let title = 'Safe Email';
  let color = '#10b981';
  let bgColor = '#d1fae5';
  let message = 'This email passed all security checks and is safe to read.';

  if (verdict === 'phishing' || action === 'delete') {
    status = 'danger';
    icon = '🚨';
    title = '⚠️ PHISHING DETECTED!';
    color = '#dc2626';
    bgColor = '#fee2e2';
    message = 'This email appears to be a phishing attempt. Do not click any links or provide personal information.';
  } else if (verdict === 'suspicious' || action === 'quarantine') {
    status = 'warning';
    icon = '⚠️';
    title = 'Suspicious Email';
    color = '#d97706';
    bgColor = '#fef3c7';
    message = 'This email has some suspicious characteristics. Please verify the sender before interacting.';
  }

  // Create popup overlay
  const popup = document.createElement('div');
  popup.id = 'spam-shield-email-popup';
  popup.className = 'spam-shield-popup-overlay';
  popup.innerHTML = `
    <div class="spam-shield-popup-content ${status}">
      <div class="spam-shield-popup-header" style="background-color: ${bgColor}; border-left: 4px solid ${color};">
        <div class="spam-shield-popup-icon" style="font-size: 48px;">${icon}</div>
        <h2 style="color: ${color}; margin: 16px 0 8px 0;">${title}</h2>
        <p style="color: #374151; margin: 0;">${message}</p>
      </div>
      <div class="spam-shield-popup-body">
        <div class="spam-shield-popup-detail">
          <strong>Analysis:</strong>
          <span>${reason || 'Email security analysis completed'}</span>
        </div>
        ${result.auth_score !== undefined ? `
          <div class="spam-shield-popup-detail">
            <strong>Security Score:</strong>
            <span>${result.auth_score}/100</span>
          </div>
        ` : ''}
        ${result.urls_analyzed !== undefined ? `
          <div class="spam-shield-popup-detail">
            <strong>Links Scanned:</strong>
            <span>${result.urls_analyzed}</span>
          </div>
        ` : ''}
      </div>
      <div class="spam-shield-popup-footer">
        <button class="spam-shield-popup-btn primary" id="spam-shield-popup-close">
          I Understand
        </button>
        <button class="spam-shield-popup-btn secondary" id="spam-shield-popup-details">
          More Details
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(popup);

  // Add event listeners
  document.getElementById('spam-shield-popup-close').addEventListener('click', () => {
    popup.classList.add('spam-shield-fade-out');
    setTimeout(() => popup.remove(), 300);
  });

  document.getElementById('spam-shield-popup-details').addEventListener('click', () => {
    popup.classList.add('spam-shield-fade-out');
    setTimeout(() => {
      popup.remove();
      showDetailsPopup(result);
    }, 300);
  });

  // Auto-close after 10 seconds (for safe emails only)
  if (status === 'safe') {
    setTimeout(() => {
      if (popup.parentNode) {
        popup.classList.add('spam-shield-fade-out');
        setTimeout(() => popup.remove(), 300);
      }
    }, 10000);
  }

  // Fade in animation
  setTimeout(() => {
    popup.classList.add('spam-shield-fade-in');
  }, 10);
}

// ============================================
// ERROR POPUPS
// ============================================
function showAuthRequiredPopup() {
  // Only show once per page load
  if (authPopupShown) {
    console.log('Auth popup already shown, skipping...');
    return;
  }
  
  authPopupShown = true;
  
  const popup = document.createElement('div');
  popup.id = 'spam-shield-error-popup';
  popup.className = 'spam-shield-popup-overlay';
  popup.innerHTML = `
    <div class="spam-shield-popup-content warning">
      <div class="spam-shield-popup-header" style="background-color: #fef3c7; border-left: 4px solid #f59e0b;">
        <div class="spam-shield-popup-icon" style="font-size: 48px;">🔐</div>
        <h2 style="color: #d97706; margin: 16px 0 8px 0;">Login Required</h2>
        <p style="color: #374151; margin: 0;">You need to login to Spam Shield to analyze emails.</p>
      </div>
      <div class="spam-shield-popup-body">
        <div class="spam-shield-popup-detail">
          <strong>Steps to login:</strong>
          <ol style="margin: 8px 0; padding-left: 20px;">
            <li>Click the Spam Shield extension icon</li>
            <li>Click "Login to Spam Shield"</li>
            <li>Login with your account</li>
            <li>Refresh this page</li>
          </ol>
        </div>
      </div>
      <div class="spam-shield-popup-footer">
        <button id="spam-shield-auth-close" class="spam-shield-popup-btn primary">Got it</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(popup);
  
  document.getElementById('spam-shield-auth-close').addEventListener('click', () => {
    popup.classList.add('spam-shield-fade-out');
    setTimeout(() => popup.remove(), 300);
  });
  
  setTimeout(() => popup.classList.add('spam-shield-fade-in'), 10);
}

function showExtensionReloadPopup() {
  const popup = document.createElement('div');
  popup.id = 'spam-shield-reload-popup';
  popup.className = 'spam-shield-popup-overlay';
  popup.innerHTML = `
    <div class="spam-shield-popup-content warning">
      <div class="spam-shield-popup-header" style="background-color: #dbeafe; border-left: 4px solid #3b82f6;">
        <div class="spam-shield-popup-icon" style="font-size: 48px;">🔄</div>
        <h2 style="color: #2563eb; margin: 16px 0 8px 0;">Extension Updated</h2>
        <p style="color: #374151; margin: 0;">Spam Shield extension was reloaded. Please refresh this page.</p>
      </div>
      <div class="spam-shield-popup-body">
        <div class="spam-shield-popup-detail">
          <strong>What happened?</strong>
          <p style="margin: 8px 0;">The extension was reloaded or updated while this page was open.</p>
        </div>
        <div class="spam-shield-popup-detail">
          <strong>Solution:</strong>
          <p style="margin: 8px 0;">Click the button below to refresh this page, or press <kbd>F5</kbd>.</p>
        </div>
      </div>
      <div class="spam-shield-popup-footer">
        <button id="spam-shield-refresh-btn" class="spam-shield-popup-btn primary">Refresh Page</button>
        <button id="spam-shield-reload-close" class="spam-shield-popup-btn">Dismiss</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(popup);
  
  document.getElementById('spam-shield-refresh-btn').addEventListener('click', () => {
    window.location.reload();
  });
  
  document.getElementById('spam-shield-reload-close').addEventListener('click', () => {
    popup.classList.add('spam-shield-fade-out');
    setTimeout(() => popup.remove(), 300);
  });
  
  setTimeout(() => popup.classList.add('spam-shield-fade-in'), 10);
}

// ============================================
// INBOX LIST INDICATORS
// ============================================
function observeInboxList() {
  const observer = new MutationObserver(() => {
    addInboxIndicators();
  });

  const inboxList = document.querySelector('div[role="main"] table');
  if (inboxList) {
    observer.observe(inboxList, {
      childList: true,
      subtree: true
    });
  }
}

async function addInboxIndicators() {
  const emailRows = document.querySelectorAll(GMAIL_SELECTORS.EMAIL_ROW);
  
  emailRows.forEach((row) => {
    // Check if already processed
    if (row.classList.contains('spam-shield-processed')) return;
    
    // Mark as processed
    row.classList.add('spam-shield-processed');
    
    // Add small indicator icon (can be expanded based on cached results)
    const iconCell = row.querySelector('td.apU');
    if (iconCell && !iconCell.querySelector('.spam-shield-mini-icon')) {
      const miniIcon = document.createElement('span');
      miniIcon.className = 'spam-shield-mini-icon';
      miniIcon.textContent = '🛡️';
      miniIcon.title = 'Protected by Spam Shield';
      iconCell.appendChild(miniIcon);
    }
  });
}

// ============================================
// START
// ============================================
// Check if we're on a Gmail page
function isGmailPage() {
  return window.location.hostname === 'mail.google.com' && 
         (window.location.pathname.includes('/mail/') || window.location.pathname === '/');
}

// Wait for Gmail to fully load
if (isGmailPage()) {
  // Try to initialize immediately
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(init, 1000);
  } else {
    window.addEventListener('load', () => {
      setTimeout(init, 1000);
    });
  }
  
  // Also try after a delay in case Gmail loads slowly
  setTimeout(() => {
    if (!currentEmailId) {
      init();
    }
  }, 3000);
}

// Re-initialize on navigation
window.addEventListener('hashchange', () => {
  currentEmailId = null;
  setTimeout(handleEmailOpened, 500);
});

// Re-initialize on popstate (back/forward)
window.addEventListener('popstate', () => {
  currentEmailId = null;
  setTimeout(handleEmailOpened, 500);
});

