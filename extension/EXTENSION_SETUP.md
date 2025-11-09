# 🛡️ Extension Setup & Troubleshooting Guide

## Quick Setup (5 Minutes)

### Step 1: Load Extension
1. Open `chrome://extensions/` in Chrome
2. Enable **"Developer mode"** (toggle in top-right)
3. Click **"Load unpacked"**
4. Select `spam_shield/extension/` folder
5. Extension should appear with ID

### Step 2: Login to Web App
1. Go to `http://localhost:5173`
2. Login with your account
3. This will automatically sync auth with extension

### Step 3: Test Extension
1. Go to `https://mail.google.com`
2. Open any email
3. Wait 2-3 seconds
4. Look for spam indicator badge

---

## Troubleshooting Extension Issues

### Issue: No Popup Showing / Blank Popup

**Symptoms:** Click extension icon, nothing shows or blank screen

**Solutions:**

1. **Check if logged in:**
   - Go to `http://localhost:5173/login`
   - Login with your account
   - Extension should sync automatically

2. **Check extension console:**
   ```
   chrome://extensions/
   → Find "Spam Shield"
   → Click "Service Worker" link
   → Check console for errors
   ```

3. **Manually reload extension:**
   ```
   chrome://extensions/
   → Click refresh icon on Spam Shield
   ```

4. **Check backend is running:**
   ```bash
   # Terminal - should show Django running
   cd backend/spam_shield
   python manage.py runserver
   ```

---

### Issue: No Spam Indicators on Emails

**Symptoms:** Open email in Gmail, no badge/indicator appears

**Solutions:**

1. **Check content script loaded:**
   - Open Gmail: `https://mail.google.com`
   - Press F12 (DevTools)
   - Go to Console tab
   - Look for: `"🛡️ Spam Shield Gmail extension loaded!"`
   - If not there, extension not injecting

2. **Verify extension permissions:**
   ```
   chrome://extensions/
   → Spam Shield → Details
   → Scroll to "Permissions"
   → Should see: "Read and change data on mail.google.com"
   ```

3. **Check if you're on correct Gmail view:**
   - Extension works on: `https://mail.google.com/mail/u/0/`
   - NOT on: `https://mail.google.com` (landing page)
   - Open an actual email thread

4. **Check backend API:**
   - Open browser console (F12)
   - Look for API errors
   - Should see POST to `http://localhost:8000/api/extension/analyze`

5. **Test API manually:**
   ```bash
   # In terminal
   curl -X GET http://localhost:8000/api/extension/health
   # Should return: {"status":"ok"}
   ```

---

### Issue: "Not authenticated" Error

**Symptoms:** Extension shows "Not authenticated" or API returns 401

**Solutions:**

1. **Re-login:**
   - Go to `http://localhost:5173/logout`
   - Then `http://localhost:5173/login`
   - Login again
   - Extension should auto-sync

2. **Check token in storage:**
   ```javascript
   // In browser console on localhost:5173
   chrome.storage.local.get(['spam_shield_token'], (result) => {
     console.log('Token:', result.spam_shield_token ? 'EXISTS' : 'MISSING');
   });
   ```

3. **Manually sync token:**
   ```javascript
   // In browser console on localhost:5173 (after login)
   const token = await supabase.auth.getSession();
   await chrome.storage.local.set({
     'spam_shield_token': token.data.session?.access_token
   });
   console.log('Token synced!');
   ```

---

### Issue: Extension Popup Shows But No Stats

**Symptoms:** Popup opens but shows "—" or loading forever

**Solutions:**

1. **Connect email account:**
   - Click extension icon
   - Click "Connect Gmail" or "Connect Outlook"
   - Complete OAuth flow

2. **Check backend connection:**
   ```javascript
   // In extension console (chrome://extensions/ → Service Worker)
   fetch('http://localhost:8000/api/extension/health')
     .then(r => r.json())
     .then(console.log);
   // Should return: {"status":"ok"}
   ```

3. **Check CORS settings:**
   - Backend must allow requests from extension
   - In `backend/spam_shield/spam_shield/settings.py`:
   ```python
   CORS_ALLOW_ALL_ORIGINS = True  # For development
   ```

---

### Issue: OAuth Connection Fails

**Symptoms:** Click "Connect Gmail/Outlook", error or redirect fails

**Solutions:**

1. **Check OAuth credentials:**
   - File: `backend/.env`
   - Must have: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - Must have: `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`

2. **Check redirect URLs:**
   - In Google Cloud Console
   - Authorized redirect URIs must include:
     - `http://localhost:8000/oauth/google/callback/`
     - `http://localhost:5173/oauth/google/callback`

3. **Use web app instead:**
   - Go to `http://localhost:5173/dashboard`
   - Connect accounts from web dashboard
   - Extension will use same connected accounts

---

## Detailed Debugging Steps

### Debug Content Script (Gmail Integration)

1. **Open Gmail:** `https://mail.google.com`
2. **Open DevTools:** Press F12
3. **Go to Console tab**
4. **Open an email**
5. **Look for these logs:**
   ```
   🛡️ Spam Shield Gmail extension loaded!
   📧 Email opened: [subject]
   ✅ Analysis complete
   ```

6. **If no logs:**
   ```javascript
   // Type in console:
   console.log('Content script check:', typeof handleEmailOpened);
   // Should return: "function"
   ```

7. **If returns "undefined":**
   - Content script not injected
   - Reload extension: `chrome://extensions/` → refresh
   - Reload Gmail page

### Debug Background Worker (API Communication)

1. **Go to:** `chrome://extensions/`
2. **Find Spam Shield**
3. **Click:** "Service Worker" link
4. **Console opens** - This is background worker console
5. **Look for logs:**
   ```
   🛡️ Spam Shield service worker loaded!
   📩 Message received: ANALYZE_EMAIL
   ```

6. **Test API manually:**
   ```javascript
   // In service worker console
   fetch('http://localhost:8000/api/extension/health', {
     headers: {'Content-Type': 'application/json'}
   })
   .then(r => r.json())
   .then(console.log)
   .catch(console.error);
   ```

### Debug Extension Popup

1. **Click extension icon** (in toolbar)
2. **Popup should open**
3. **Right-click on popup** → "Inspect"
4. **DevTools for popup opens**
5. **Check console for errors**
6. **Check if elements loaded:**
   ```javascript
   // In popup console
   console.log(document.getElementById('authView'));
   // Should return: HTMLElement or null
   ```

---

## Force Indicator to Show (Testing)

If you want to test that indicators work, add this to Gmail console:

```javascript
// Create test indicator
const toolbar = document.querySelector('div.iH');
if (toolbar) {
  const indicator = document.createElement('div');
  indicator.id = 'spam-shield-indicator';
  indicator.innerHTML = `
    <div style="padding:8px 16px; background:#10b981; color:white; border-radius:8px; display:inline-block; margin:8px 0;">
      <span style="font-size:18px;">✅</span>
      <span style="margin-left:8px; font-weight:600;">Safe Email</span>
    </div>
  `;
  toolbar.insertBefore(indicator, toolbar.firstChild);
  console.log('Test indicator added!');
}
```

If this works, the content script DOM manipulation is fine, issue is with email detection or API.

---

## Common Error Messages

### "CORS policy: No 'Access-Control-Allow-Origin'"

**Fix:** Backend CORS not configured

```python
# backend/spam_shield/spam_shield/settings.py
CORS_ALLOW_ALL_ORIGINS = True  # Add this
```

Restart backend after change.

### "Failed to fetch"

**Fix:** Backend not running

```bash
cd backend/spam_shield
python manage.py runserver
```

### "Extension context invalidated"

**Fix:** Extension was reloaded

- Just reload the Gmail page
- Extension will re-inject

### "Cannot read property 'sendMessage' of undefined"

**Fix:** Chrome API not available

- Only works in Chrome/Edge/Brave
- Won't work in Safari or Firefox (need different build)

---

## Verification Checklist

Before reporting issues, verify:

- [ ] Backend running on `http://localhost:8000`
- [ ] Frontend running on `http://localhost:5173`
- [ ] Logged in to web app
- [ ] Extension loaded in `chrome://extensions/`
- [ ] Developer mode enabled
- [ ] No console errors in:
  - Gmail page (F12)
  - Extension service worker
  - Extension popup
- [ ] On actual Gmail page (not landing page)
- [ ] Opened an email (not just inbox)
- [ ] Waited 3-5 seconds for analysis

---

## Quick Reset (Nuclear Option)

If nothing works:

1. **Remove extension:**
   ```
   chrome://extensions/ → Remove Spam Shield
   ```

2. **Clear storage:**
   ```javascript
   // In console on localhost:5173
   chrome.storage.local.clear();
   localStorage.clear();
   ```

3. **Logout:**
   ```
   http://localhost:5173/logout
   ```

4. **Restart all services:**
   ```bash
   # Kill backend, Celery, frontend
   # Restart all three
   ```

5. **Reload extension:**
   ```
   chrome://extensions/ → Load unpacked → Select extension/
   ```

6. **Login again:**
   ```
   http://localhost:5173/login
   ```

7. **Test:**
   ```
   Go to Gmail → Open email → Wait
   ```

---

## Still Not Working?

Check these files for issues:

1. **Backend logs:**
   ```bash
   # Terminal where backend is running
   # Look for POST requests to /api/extension/analyze
   ```

2. **Extension manifest:**
   ```json
   // extension/manifest.json
   // Verify "content_scripts" section has Gmail URLs
   ```

3. **Extension permissions:**
   ```
   chrome://extensions/
   → Spam Shield → Details
   → Should have "Read and change data" permissions
   ```

---

**Need more help? Check the console logs - they're your best friend!**

