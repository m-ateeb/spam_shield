# 🛡️ Spam Shield Browser Extension

AI-powered spam and phishing protection for Gmail and Outlook web interfaces.

## 🚀 Features

- **Real-time Email Scanning**: Automatically analyzes emails as you open them
- **Spam Detection**: Uses SPF, DKIM, DMARC authentication and URL reputation analysis
- **Visual Indicators**: Clear badges showing email safety status
- **Quarantine Management**: Review and manage quarantined emails
- **Multi-Provider Support**: Works with both Gmail and Outlook
- **Privacy-Focused**: Email content analyzed securely, not stored permanently

## 📋 Prerequisites

1. **Backend Server**: Spam Shield Django backend running (default: http://localhost:8000)
2. **Web Dashboard**: Frontend dashboard for authentication (default: http://localhost:5173)
3. **Browser**: Chrome, Edge, or Firefox (Manifest V3 compatible)

## 🔧 Installation

### Step 1: Load Extension in Developer Mode

#### Chrome/Edge:
1. Open `chrome://extensions/` (or `edge://extensions/`)
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Select the `extension` folder from your Spam Shield project
5. The extension should now appear in your toolbar

#### Firefox:
1. Open `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Navigate to `extension/manifest.json`
4. Select the file

### Step 2: Initial Setup

1. **Click the extension icon** in your browser toolbar
2. **Login** to your Spam Shield account
   - This will open the web dashboard
   - If you don't have an account, sign up first
3. **Connect your email account**:
   - Click "Connect Gmail" or "Connect Outlook"
   - Complete the OAuth authorization flow
   - Grant permission to read emails

### Step 3: Start Using

1. Open **Gmail** (mail.google.com) or **Outlook** (outlook.live.com/outlook.office365.com)
2. Open any email
3. The extension will automatically analyze it and show a security badge:
   - ✅ **Safe** (Green) - Email passed all checks
   - ⚠️ **Suspicious** (Orange) - Email has some red flags
   - 🚨 **Phishing** (Red) - Dangerous email detected

## ⚙️ Configuration

### Settings
Right-click the extension icon → **Options** to configure:

**Protection Settings:**
- Auto-Quarantine Suspicious Emails
- Real-Time Email Scanning
- Strict Mode (more aggressive detection)

**Notifications:**
- Enable/disable spam detection alerts
- Quarantine notifications
- Phishing alerts

**API Configuration:**
- Backend API URL (change if not using localhost)
- Frontend Dashboard URL

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   Gmail/Outlook Web Interface      │
│   (Content Scripts Injected)        │
└─────────────┬───────────────────────┘
              │ Email Data
              ▼
┌─────────────────────────────────────┐
│   Extension Background Worker       │
│   (API Communication)                │
└─────────────┬───────────────────────┘
              │ HTTP Request
              ▼
┌─────────────────────────────────────┐
│   Django Backend API                │
│   ├─ Email Authentication (SPF/DKIM)│
│   ├─ URL Reputation Analysis        │
│   └─ Decision Engine                │
└─────────────┬───────────────────────┘
              │ Results
              ▼
┌─────────────────────────────────────┐
│   Supabase Database                 │
│   (Email logs, quarantine, stats)   │
└─────────────────────────────────────┘
```

## 📂 File Structure

```
extension/
├── manifest.json                 # Extension configuration
├── background/
│   └── service-worker.js        # API communication & background tasks
├── content/
│   ├── gmail.js                 # Gmail-specific content script
│   ├── outlook.js               # Outlook-specific content script
│   └── styles.css               # Injected UI styles
├── popup/
│   ├── popup.html               # Extension popup UI
│   ├── popup.js                 # Popup logic
│   └── popup.css                # Popup styles
├── options/
│   ├── options.html             # Settings page
│   ├── options.js               # Settings logic
│   └── options.css              # Settings styles
└── assets/
    └── icons/                   # Extension icons (16, 32, 48, 128px)
```

## 🔌 API Endpoints Used

The extension communicates with these backend endpoints:

- `POST /api/extension/analyze` - Real-time email analysis
- `GET /api/extension/health` - Health check
- `GET /api/quarantine/list/` - Get quarantined emails
- `POST /api/quarantine/release/` - Release email from quarantine
- `POST /api/quarantine/delete/` - Delete quarantined email
- `GET /api/dashboard/summary/` - Get stats
- `POST /oauth/google/` - Connect Gmail
- `POST /oauth/microsoft/` - Connect Outlook

## 🛠️ Development

### Making Changes

1. Edit extension files
2. Reload extension:
   - Chrome: Go to `chrome://extensions/` → Click refresh icon
   - Firefox: Click "Reload" in `about:debugging`
3. Refresh the Gmail/Outlook page to see changes

### Debugging

**Content Scripts:**
- Open Gmail/Outlook
- Right-click → "Inspect"
- Check Console for logs (prefixed with 🛡️)

**Background Worker:**
- Go to `chrome://extensions/`
- Click "Service Worker" under Spam Shield
- Check console logs

**Popup:**
- Right-click extension icon → "Inspect popup"

### Testing

1. **Safe Email Test**: Open a legitimate email → Should show ✅ green badge
2. **Suspicious Email Test**: Create test with failed SPF/DKIM → Should show ⚠️ orange
3. **Phishing Test**: Email with known malicious URL → Should show 🚨 red

## 🔒 Security & Privacy

- **OAuth Tokens**: Stored encrypted in local storage
- **Email Content**: Sent to backend for analysis, not permanently stored
- **Metadata Only**: Only sender, subject, and URLs retained for security logs
- **User Control**: Revoke access anytime from Gmail/Outlook account settings

## 🐛 Troubleshooting

### Extension not loading
- Ensure manifest.json is valid
- Check browser console for errors
- Verify all required files exist

### No spam indicators showing
1. Check if you're logged in (click extension icon)
2. Verify email account is connected
3. Check backend server is running
4. Open browser console for error messages

### OAuth connection fails
1. Ensure backend URL is correct in settings
2. Check CORS settings on backend
3. Verify OAuth credentials are configured in backend `.env`

### "Not authenticated" error
1. Login to web dashboard first
2. Extension should sync authentication automatically
3. Try logout and login again

## 📝 Configuration Files

### Update Backend URL (Production)

Edit `extension/background/service-worker.js`:
```javascript
const CONFIG = {
  API_BASE_URL: 'https://your-backend.com',  // Change this
  FRONTEND_URL: 'https://your-frontend.com'  // Change this
};
```

Or use the **Options page** in the extension.

### Enable Production Icons

Replace placeholder icons in `extension/assets/icons/` with actual PNG files:
- `icon16.png` (16x16px)
- `icon32.png` (32x32px)
- `icon48.png` (48x48px)
- `icon128.png` (128x128px)

## 🚀 Publishing

### Chrome Web Store
1. Create a developer account
2. Zip the extension folder
3. Upload to Chrome Web Store Developer Dashboard
4. Fill in store listing details
5. Submit for review

### Firefox Add-ons
1. Create a Mozilla account
2. Zip extension folder
3. Upload to addons.mozilla.org
4. Submit for review

## 📄 License

See main project LICENSE file.

## 🤝 Contributing

See main project CONTRIBUTING.md file.

## 📧 Support

For issues or questions:
- GitHub Issues: [project-repo]/issues
- Email: support@spamshield.com
- Documentation: http://localhost:5173/features

---

**Built with ❤️ by the Spam Shield Team**

