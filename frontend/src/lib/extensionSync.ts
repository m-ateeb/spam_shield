/**
 * Extension Auth Sync Helper
 * Syncs authentication state with the browser extension
 */

// Type guard to check if Chrome API is available
const isChromeExtensionAvailable = (): boolean => {
  return typeof window !== 'undefined' && 
         typeof (window as any).chrome !== 'undefined' && 
         typeof (window as any).chrome.storage !== 'undefined';
};

// Extension ID (will be filled after publishing, for now use runtime)
const EXTENSION_ID = 'YOUR_EXTENSION_ID'; // Replace with actual ID after publishing

/**
 * Send authentication token to extension
 * Non-blocking - runs in background without blocking UI
 */
export const syncAuthWithExtension = (token: string | null, user: any) => {
  // Run async without blocking
  Promise.resolve().then(async () => {
    try {
      // For development, use storage API instead of messaging
      if (isChromeExtensionAvailable()) {
        await (window as any).chrome.storage.local.set({
          'spam_shield_token': token,
          'spam_shield_user': user ? {
            id: user.id,
            email: user.email,
            role: user.user_metadata?.role || 'user'
          } : null
        });
        console.log('✅ Auth synced with extension');
        return true;
      }
    } catch (error) {
      console.log('Extension not available:', error);
      return false;
    }
  });
};

/**
 * Clear extension auth
 * Non-blocking - runs in background without blocking UI
 */
export const clearExtensionAuth = () => {
  // Run async without blocking
  Promise.resolve().then(async () => {
    try {
      if (isChromeExtensionAvailable()) {
        await (window as any).chrome.storage.local.remove(['spam_shield_token', 'spam_shield_user']);
        console.log('✅ Extension auth cleared');
        return true;
      }
    } catch (error) {
      console.log('Extension not available:', error);
      return false;
    }
  });
};

