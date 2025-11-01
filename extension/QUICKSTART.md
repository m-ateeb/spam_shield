# 🚀 Quick Start Guide

## 1. Prerequisites Check

Before installing the extension, ensure:

- [ ] **Backend is running**: `http://localhost:8000`
- [ ] **Frontend is running**: `http://localhost:5173`
- [ ] **You have a user account** (sign up at frontend if not)

### Start Backend (if not running):
```bash
cd backend/spam_shield
python manage.py runserver
```

### Start Frontend (if not running):
```bash
cd frontend
npm run dev
```

### Start Celery Worker (for async tasks):
```bash
cd backend/spam_shield
celery -A spam_shield worker --loglevel=info --pool=solo
```

## 2. Install Extension (2 minutes)

### Chrome/Edge:
1. Open browser and go to: `chrome://extensions/`
2. Turn ON "Developer mode" (toggle in top-right)
3. Click **"Load unpacked"**
4. Navigate to your project and select the **`extension`** folder
5. Click "Select Folder"

✅ Extension installed! You should see it in your toolbar.

### Firefox:
1. Go to: `about:debugging#/runtime/this-firefox`
2. Click **"Load Temporary Add-on"**
3. Navigate to `extension/manifest.json`
4. Select it

## 3. First-Time Setup (3 minutes)

### Step 1: Login
1. Click the 🛡️ extension icon in toolbar
2. Click **"Login to Spam Shield"**
3. Browser opens to `http://localhost:5173/login`
4. Login with your credentials
5. Extension popup should now show stats

### Step 2: Connect Email
1. Click extension icon again
2. Click **"Connect Gmail"** or **"Connect Outlook"**
3. Complete OAuth authorization
4. Grant permissions when prompted

✅ Setup complete!

## 4. Test It Out (1 minute)

### Gmail Test:
1. Go to `https://mail.google.com`
2. Open any email
3. Wait 2-3 seconds
4. Look for the Spam Shield badge at the top
5. Should show: ✅ Safe, ⚠️ Suspicious, or 🚨 Phishing

### Outlook Test:
1. Go to `https://outlook.live.com` or `outlook.office365.com`
2. Open any email
3. Look for security banner at top

## 5. View Stats

Click extension icon anytime to see:
- Total emails scanned
- Spam blocked
- Quarantined emails
- Quick actions

## 🐛 Troubleshooting

### "Not authenticated" error
**Solution**: 
1. Click extension icon
2. Click "Login to Spam Shield"
3. Login on web dashboard
4. Refresh Gmail/Outlook page

### No badge showing on emails
**Solution**:
1. Open browser DevTools (F12)
2. Look for errors in Console
3. Common issues:
   - Backend not running → Start backend
   - Not logged in → Login via extension popup
   - No account connected → Connect Gmail/Outlook

### "Failed to analyze email"
**Solution**:
1. Check backend is running: Visit `http://localhost:8000/admin/`
2. Check CORS settings (backend should allow requests from extension)
3. Check browser console for specific error

### Extension not loading
**Solution**:
1. Check all files exist in `extension/` folder
2. Verify `manifest.json` is valid
3. Remove and re-add extension
4. Check browser console for errors

## 📊 What Happens Behind the Scenes?

```
You open email in Gmail
    ↓
Content script detects email open
    ↓
Extracts: subject, sender, body, links
    ↓
Sends to background worker
    ↓
Background worker → Backend API
    ↓
Backend analyzes:
  - SPF/DKIM authentication
  - URL reputation (Google Safe Browsing, URLHaus)
  - Sender reputation
    ↓
Decision engine classifies:
  - Safe ✅
  - Suspicious ⚠️
  - Phishing 🚨
    ↓
Result sent back to extension
    ↓
Badge displayed on email
```

## 🎯 Next Steps

- [ ] Configure settings (right-click icon → Options)
- [ ] Enable notifications for spam alerts
- [ ] Review quarantined emails in dashboard
- [ ] Customize protection level (strict mode)

## 📝 Notes

- Extension stores minimal data locally (auth token, settings)
- Email content is not stored permanently
- You can revoke access anytime from Gmail/Outlook settings
- Works offline after initial setup (cached results)

## 🎨 Customize (Optional)

### Change Icon
Replace files in `extension/assets/icons/` with your own PNG icons

### Change Colors
Edit `extension/content/styles.css`:
- Green badge: Line with `#10b981`
- Orange badge: Line with `#f59e0b`
- Red badge: Line with `#ef4444`

### Adjust Detection Sensitivity
Go to extension Options → Enable "Strict Mode"

---

**Questions? Check the full README.md or open an issue on GitHub**

