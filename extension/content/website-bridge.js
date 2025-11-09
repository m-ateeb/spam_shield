/**
 * Website Bridge Content Script
 * Runs on localhost:5173 to receive auth from website
 */

console.log('🌉 Spam Shield website bridge loaded');

// Listen for messages from the website
window.addEventListener('message', (event) => {
  // Only accept messages from our frontend
  if (event.origin !== 'http://localhost:5173' && event.origin !== 'http://127.0.0.1:5173') {
    return;
  }

  if (event.data.type === 'SPAM_SHIELD_AUTH') {
    console.log('🔐 Received auth from website:', event.data.user);
    
    // Forward to background worker
    chrome.runtime.sendMessage({
      action: 'SET_AUTH',
      data: {
        token: event.data.token,
        user: event.data.user
      }
    }, (response) => {
      if (response?.success) {
        console.log('✅ Auth stored in extension');
        // Notify website of success
        window.postMessage({ type: 'SPAM_SHIELD_AUTH_SUCCESS' }, '*');
      }
    });
  }
  
  if (event.data.type === 'SPAM_SHIELD_LOGOUT') {
    console.log('🚪 Logout request from website - clearing extension auth only');
    // Only clear extension storage, don't call backend logout
    chrome.runtime.sendMessage({ action: 'LOGOUT' });
  }
});

// Signal to website that extension is ready
window.postMessage({ type: 'SPAM_SHIELD_READY' }, '*');

