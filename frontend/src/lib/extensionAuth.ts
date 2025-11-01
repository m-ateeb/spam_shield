/**
 * Extension Auth Sync via PostMessage
 * Uses content script bridge for reliable communication
 */

export const syncTokenToExtension = async (token: string, userEmail: string) => {
  return new Promise<void>((resolve) => {
    console.log('🔄 Syncing auth to extension...');
    
    // Listen for success response
    const handleResponse = (event: MessageEvent) => {
      if (event.data.type === 'SPAM_SHIELD_AUTH_SUCCESS') {
        console.log('✅ Auth synced to extension successfully!');
        window.removeEventListener('message', handleResponse);
        resolve();
      }
    };
    
    window.addEventListener('message', handleResponse);
    
    // Send auth to extension via postMessage
    window.postMessage({
      type: 'SPAM_SHIELD_AUTH',
      token: token,
      user: { email: userEmail }
    }, '*');
    
    // Timeout after 2 seconds
    setTimeout(() => {
      window.removeEventListener('message', handleResponse);
      console.log('⚠️ Extension auth sync timed out (extension may not be installed)');
      resolve();
    }, 2000);
  });
};

export const clearExtensionAuth = async () => {
  try {
    window.postMessage({
      type: 'SPAM_SHIELD_LOGOUT'
    }, '*');
  } catch (error) {
    // Silent fail
  }
};

