/**
 * Spam Shield - Outlook Content Script
 * Monitors Outlook interface and adds spam indicators
 */

console.log('🛡️ Spam Shield Outlook extension loaded!');

// Configuration
const OUTLOOK_SELECTORS = {
  EMAIL_VIEW: 'div[role="main"]',
  EMAIL_SUBJECT: 'span[id*="SubjectLine"]',
  EMAIL_SENDER: 'span[id*="FromEmail"]',
  EMAIL_BODY: 'div[class*="ReadingPaneContents"]',
  EMAIL_HEADER: 'div[class*="ReadingPaneHeader"]',
  EMAIL_ROW: 'div[role="row"][class*="FocusZone"]'
};

let currentEmailId = null;
let analysisCache = new Map();
let authPopupShown = false; // Prevent infinite auth popups

// ============================================
// INITIALIZATION
// ============================================
function init() {
  console.log('🚀 Initializing Outlook spam detection...');
  
  // Monitor for email view changes
  observeEmailView();
  
  // Add spam indicators to inbox list
  observeInboxList();
}

// ============================================
// EMAIL VIEW MONITORING
// ============================================
function observeEmailView() {
  const observer = new MutationObserver((mutations) => {
    const emailView = document.querySelector(OUTLOOK_SELECTORS.EMAIL_BODY);
    if (emailView) {
      handleEmailOpened();
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

async function handleEmailOpened() {
  try {
    const emailData = extractEmailData();
    if (!emailData || currentEmailId === emailData.messageId) {
      return;
    }

    currentEmailId = emailData.messageId;
    console.log('📧 Email opened:', emailData.subject);

    // Check cache
    if (analysisCache.has(emailData.messageId)) {
      const cachedResult = analysisCache.get(emailData.messageId);
      displaySpamIndicator(cachedResult);
      return;
    }

    // Show loading
    showLoadingIndicator();

    // Analyze
    const response = await chrome.runtime.sendMessage({
      action: 'ANALYZE_EMAIL',
      data: emailData
    });

    if (response.error) {
      console.error('❌ Analysis error:', response.error);
      removeLoadingIndicator();
      
      // Show user-friendly error popup
      if (response.error === 'Not authenticated') {
        showAuthRequiredPopup();
      }
      return;
    }

    analysisCache.set(emailData.messageId, response.result);
    removeLoadingIndicator();
    displaySpamIndicator(response.result);

  } catch (error) {
    removeLoadingIndicator();
    
    // Handle extension context invalidation (extension was reloaded)
    if (error.message && error.message.includes('Extension context invalidated')) {
      console.log('🔄 Extension was reloaded. Please refresh this page (F5)');
      showExtensionReloadPopup();
      return;
    }
    
    console.error('❌ Error handling email:', error);
  }
}

// ============================================
// EMAIL DATA EXTRACTION
// ============================================
function extractEmailData() {
  try {
    // Extract message ID from URL or data attributes
    const messageId = extractMessageIdFromURL() || extractMessageIdFromDOM();

    const subjectElement = document.querySelector(OUTLOOK_SELECTORS.EMAIL_SUBJECT);
    const subject = subjectElement?.textContent?.trim() || '';

    const senderElement = document.querySelector(OUTLOOK_SELECTORS.EMAIL_SENDER);
    const from = senderElement?.textContent?.trim() || extractFromAlternative();

    const bodyElement = document.querySelector(OUTLOOK_SELECTORS.EMAIL_BODY);
    const bodyHtml = bodyElement?.innerHTML || '';

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
      provider: 'outlook'
    };
  } catch (error) {
    console.error('❌ Error extracting email data:', error);
    return null;
  }
}

function extractMessageIdFromURL() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('ItemID') || null;
}

function extractMessageIdFromDOM() {
  // Try multiple methods to get message ID
  const emailContainer = document.querySelector('[data-convid]');
  if (emailContainer) {
    return emailContainer.getAttribute('data-convid');
  }

  // Alternative: extract from aria-label or other attributes
  const header = document.querySelector(OUTLOOK_SELECTORS.EMAIL_HEADER);
  if (header) {
    const dataId = header.getAttribute('data-message-id');
    if (dataId) return dataId;
  }

  return null;
}

function extractFromAlternative() {
  // Alternative methods to extract sender
  const personaElement = document.querySelector('div[class*="Persona"]');
  return personaElement?.textContent?.trim() || '';
}

function extractRecipient() {
  const toElement = document.querySelector('div[aria-label*="To:"]');
  return toElement?.textContent?.replace('To:', '').trim() || '';
}

function extractDate() {
  const dateElement = document.querySelector('span[aria-label*="Received"]');
  return dateElement?.textContent?.trim() || '';
}

function generateTempId() {
  return `temp_outlook_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ============================================
// SPAM INDICATOR UI
// ============================================
function displaySpamIndicator(result) {
  const existingIndicator = document.getElementById('spam-shield-indicator-outlook');
  if (existingIndicator) {
    existingIndicator.remove();
  }

  const header = document.querySelector(OUTLOOK_SELECTORS.EMAIL_HEADER);
  if (!header) return;

  const indicator = createIndicatorElement(result);
  
  // Insert at the top of header
  const firstChild = header.firstElementChild;
  if (firstChild) {
    header.insertBefore(indicator, firstChild);
  } else {
    header.appendChild(indicator);
  }
  
  // Show prominent popup notification
  showEmailAnalysisPopup(result);
}

function createIndicatorElement(result) {
  const container = document.createElement('div');
  container.id = 'spam-shield-indicator-outlook';
  container.className = 'spam-shield-indicator outlook-style';

  const { verdict, action, reason } = result;

  let status = 'safe';
  let icon = '✅';
  let text = 'Safe Email';
  let color = '#10b981';
  let bgColor = '#d1fae5';

  if (verdict === 'phishing' || action === 'delete') {
    status = 'danger';
    icon = '🚨';
    text = 'Phishing Detected';
    color = '#dc2626';
    bgColor = '#fee2e2';
  } else if (verdict === 'suspicious' || action === 'quarantine') {
    status = 'warning';
    icon = '⚠️';
    text = 'Suspicious Email';
    color = '#d97706';
    bgColor = '#fef3c7';
  }

  container.innerHTML = `
    <div class="spam-shield-banner ${status}" style="background-color: ${bgColor}; border-left: 4px solid ${color};">
      <div class="spam-shield-content">
        <span class="spam-shield-icon" style="font-size: 20px;">${icon}</span>
        <div class="spam-shield-text-container">
          <strong style="color: ${color};">${text}</strong>
          <p style="margin: 4px 0 0 0; font-size: 12px; color: #666;">
            ${reason || 'This email passed all security checks'}
          </p>
        </div>
      </div>
      <button class="spam-shield-details-btn" style="color: ${color};">
        Details
      </button>
    </div>
  `;

  // Add event listener
  container.querySelector('.spam-shield-details-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    showDetailsPopup(result);
  });

  return container;
}

function showLoadingIndicator() {
  const header = document.querySelector(OUTLOOK_SELECTORS.EMAIL_HEADER);
  if (!header) return;

  const loader = document.createElement('div');
  loader.id = 'spam-shield-loader-outlook';
  loader.className = 'spam-shield-indicator outlook-style';
  loader.innerHTML = `
    <div class="spam-shield-banner loading" style="background-color: #f3f4f6;">
      <div class="spam-shield-content">
        <span class="spam-shield-spinner">⏳</span>
        <span style="margin-left: 8px;">Analyzing email security...</span>
      </div>
    </div>
  `;
  
  const firstChild = header.firstElementChild;
  if (firstChild) {
    header.insertBefore(loader, firstChild);
  } else {
    header.appendChild(loader);
  }
}

function removeLoadingIndicator() {
  const loader = document.getElementById('spam-shield-loader-outlook');
  if (loader) loader.remove();
}

function showDetailsPopup(result) {
  const popup = document.createElement('div');
  popup.className = 'spam-shield-details-popup';
  popup.innerHTML = `
    <div class="spam-shield-details-content">
      <div class="popup-header">
        <h3>🛡️ Spam Shield Security Analysis</h3>
        <button class="spam-shield-close-btn">×</button>
      </div>
      <div class="popup-body">
        <div class="detail-row">
          <strong>Verdict:</strong>
          <span class="detail-value">${result.verdict || 'Unknown'}</span>
        </div>
        <div class="detail-row">
          <strong>Action Taken:</strong>
          <span class="detail-value">${result.action || 'None'}</span>
        </div>
        <div class="detail-row">
          <strong>Reason:</strong>
          <span class="detail-value">${result.reason || 'N/A'}</span>
        </div>
        ${result.auth_score !== undefined ? `
          <div class="detail-row">
            <strong>Authentication Score:</strong>
            <span class="detail-value">${result.auth_score}/100</span>
          </div>
        ` : ''}
        ${result.url_analysis ? `
          <div class="detail-row">
            <strong>URL Analysis:</strong>
            <span class="detail-value">${result.url_analysis}</span>
          </div>
        ` : ''}
      </div>
    </div>
  `;

  document.body.appendChild(popup);

  popup.querySelector('.spam-shield-close-btn').addEventListener('click', () => {
    popup.remove();
  });

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
        <button class="spam-shield-popup-btn primary" id="spam-shield-popup-close-outlook">
          I Understand
        </button>
        <button class="spam-shield-popup-btn secondary" id="spam-shield-popup-details-outlook">
          More Details
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(popup);

  // Add event listeners
  document.getElementById('spam-shield-popup-close-outlook').addEventListener('click', () => {
    popup.classList.add('spam-shield-fade-out');
    setTimeout(() => popup.remove(), 300);
  });

  document.getElementById('spam-shield-popup-details-outlook').addEventListener('click', () => {
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
        <button id="spam-shield-auth-close-outlook" class="spam-shield-popup-btn primary">Got it</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(popup);
  
  document.getElementById('spam-shield-auth-close-outlook').addEventListener('click', () => {
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
        <button id="spam-shield-refresh-btn-outlook" class="spam-shield-popup-btn primary">Refresh Page</button>
        <button id="spam-shield-reload-close-outlook" class="spam-shield-popup-btn">Dismiss</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(popup);
  
  document.getElementById('spam-shield-refresh-btn-outlook').addEventListener('click', () => {
    window.location.reload();
  });
  
  document.getElementById('spam-shield-reload-close-outlook').addEventListener('click', () => {
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

  const inboxContainer = document.querySelector('div[role="list"]');
  if (inboxContainer) {
    observer.observe(inboxContainer, {
      childList: true,
      subtree: true
    });
  }
}

function addInboxIndicators() {
  const emailRows = document.querySelectorAll(OUTLOOK_SELECTORS.EMAIL_ROW);
  
  emailRows.forEach((row) => {
    if (row.classList.contains('spam-shield-processed')) return;
    
    row.classList.add('spam-shield-processed');
    
    // Add small protection icon
    const iconContainer = row.querySelector('div[class*="iconContainer"]');
    if (iconContainer && !iconContainer.querySelector('.spam-shield-mini-icon')) {
      const miniIcon = document.createElement('span');
      miniIcon.className = 'spam-shield-mini-icon';
      miniIcon.textContent = '🛡️';
      miniIcon.title = 'Protected by Spam Shield';
      miniIcon.style.fontSize = '10px';
      miniIcon.style.marginLeft = '4px';
      iconContainer.appendChild(miniIcon);
    }
  });
}

// ============================================
// START
// ============================================
setTimeout(init, 2000);

// Monitor for navigation changes in Outlook
let lastUrl = window.location.href;
setInterval(() => {
  if (window.location.href !== lastUrl) {
    lastUrl = window.location.href;
    currentEmailId = null;
    setTimeout(handleEmailOpened, 500);
  }
}, 1000);

