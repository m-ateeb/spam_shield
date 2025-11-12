# Spam Shield Backend Workflow - Complete Explanation

## Overview

Spam Shield processes emails in **two ways**:
1. **Automatic Background Processing** (via webhooks) - Processes ALL incoming emails
2. **On-Demand Extension Analysis** - Analyzes emails when you open them in Gmail/Outlook

## Why Dashboard Shows Many Emails Even If You Haven't Opened Them

**The dashboard counts ALL emails that have been processed**, not just emails you've opened. Here's why:

### Automatic Email Processing (Webhooks)

When you connect your Gmail/Outlook account:
1. **Gmail Watch** or **Outlook Webhooks** are set up
2. Every time a **new email arrives** in your inbox, a webhook notification is sent to the backend
3. The backend **automatically processes** these emails in the background using Celery tasks
4. These emails are **analyzed, classified, and stored** in the database
5. **You don't need to open them** - they're processed automatically

**Example:**
- You receive 100 emails today
- Webhooks trigger processing for all 100 emails
- All 100 are analyzed and stored
- Dashboard shows: "100 Total Emails" even if you only opened 5

### Email Processing Flow

```
New Email Arrives
    ↓
Webhook Notification (Gmail/Outlook)
    ↓
process_incoming_email.delay() [Celery Task]
    ↓
Fetch Email from Gmail/Outlook API
    ↓
save_email() - Extract & Validate
    ↓
run_post_process_pipeline.delay() [Celery Task]
    ↓
run_rule_based_classification()
    ↓
Quarantine if needed
```

## Complete Backend Workflow

### Module 1: Email Fetching (`tasks.py`)

**Entry Point:** `process_incoming_email(email, provider, history_id)`

**What it does:**
1. Gets valid OAuth token for the email account
2. Fetches recent emails from Gmail/Outlook API
3. For each email, calls `save_email()` to process it

**Gmail Processing:**
- Fetches last 10 emails (configurable via `EMAIL_BATCH_SIZE`)
- Gets full email data including raw MIME for authentication checks

**Outlook Processing:**
- Fetches recent messages from Microsoft Graph API
- Gets full email data including raw MIME

### Module 2: Email Authentication (`email_validator.py`)

**Function:** `validate_email_authenticity(raw_email, domain, message_id)`

**What it checks:**
1. **SPF (Sender Policy Framework)**
   - Verifies sender's IP is authorized by domain
   - Result: `pass`, `fail`, `none`, `unknown`

2. **DKIM (DomainKeys Identified Mail)**
   - Verifies email signature using cryptographic keys
   - Result: `pass`, `fail`, `none`, `unknown`

3. **DMARC (Domain-based Message Authentication)**
   - Checks domain's email authentication policy
   - Result: `pass`, `fail`, `quarantine`, `reject`, `none`

4. **Authentication Score Calculation**
   - Combines SPF, DKIM, DMARC results
   - Score range: 0-100
   - Higher score = more legitimate

**Score Calculation:**
- Each `pass` = +33 points
- Each `fail` = 0 points
- Each `none` = +10 points
- Each `unknown` = +5 points
- Maximum: 100 points

### Module 3: URL Reputation Analysis (`url_reputation.py`)

**Function:** `analyze_url(url, email_id)`

**What it checks:**
1. **Google Safe Browsing API**
   - Checks if URL is in Google's malware/phishing database
   - Returns: `safe`, `malicious`, `unknown`

2. **URLHaus Database**
   - Checks if URL is flagged as malicious
   - Returns: `safe`, `malicious`, `unknown`

3. **URLScan.io** (Async)
   - Submits URL for deep scanning
   - Initially returns: `pending`
   - Polls for results every 15 seconds
   - Final verdict: `safe`, `suspicious`, `malicious`

**URL Analysis Flow:**
```
Extract URLs from Email Body
    ↓
For each URL:
    Check Google Safe Browsing → If malicious, stop
    Check URLHaus → If malicious, stop
    Submit to URLScan.io → Get scan_id
    ↓
poll_urlscan_result.delay(scan_id, email_id, url) [After 15s]
    ↓
Poll URLScan API until result ready
    ↓
Update URLAnalysis record
    ↓
If all URLs complete → Re-run classification
```

### Module 4: Decision Engine (`decision_engine.py`)

**Function:** `run_rule_based_classification(email_id)`

**Classification Rules:**

1. **Malicious URLs Detected**
   - Verdict: `phishing`
   - Action: `delete`
   - Confidence: 85-95%

2. **Auth Score < 20**
   - Verdict: `phishing`
   - Action: `delete`
   - Confidence: 80-95% (lower score = higher confidence)

3. **Auth Score 20-40**
   - Verdict: `suspicious`
   - Action: `quarantine`
   - Confidence: 65-90%

4. **Auth Score >= 40**
   - Verdict: `safe`
   - Action: `allow`
   - Confidence: 75-95%

**Classification Process:**
```
Check if URL analysis complete
    ↓ (If URLs pending, return None - don't classify)
Check authentication results exist
    ↓ (If no auth results, return None)
Calculate verdict based on rules
    ↓
Create/Update ClassificationResult
    ↓
If verdict is phishing/suspicious:
    quarantine_email() → Add to quarantine
    execute_email_action() → Delete/move in Gmail/Outlook
```

### Module 5: Quarantine System

**Function:** `quarantine_email(email_obj, action, reason)`

**What it does:**
1. Creates `QuarantinedEmail` record with status `pending`
2. Marks email as `is_suspicious = True`
3. Logs the quarantine action

**Important:** 
- All quarantined emails have status `pending` (even phishing)
- This allows users to review them in the quarantine list
- The actual email deletion/moving happens via `execute_email_action()`

**Quarantine List:**
- Shows all emails with `QuarantinedEmail` records
- Filters out duplicates and incomplete emails
- Only shows emails with complete classification

## Extension Analysis Flow

When you open an email in Gmail/Outlook:

1. **Extension detects email opened**
   - Extracts: message_id, subject, from, body_html

2. **Sends to backend:** `/api/extension/analyze/`
   - Checks if email already analyzed (cached)
   - If not, performs domain-based authentication
   - Extracts and analyzes URLs
   - Runs classification

3. **Backend Response:**
   - If analysis complete: Returns verdict + `analysis_complete: true`
   - If analysis pending: Returns `verdict: 'pending'` + `analysis_complete: false`

4. **Extension Behavior:**
   - If `pending`: Starts polling every 10 seconds
   - If `complete`: Displays result and caches it
   - **Never shows phishing popup for pending results**

## Why Phishing Popup Appeared Then Changed to Safe

**Previous Issue (Now Fixed):**

1. Extension sent email for analysis
2. Backend returned preliminary result (before URL analysis complete)
3. Extension showed phishing popup
4. URL analysis completed → Classification updated
5. Extension didn't poll for updates → Still showing old result

**Fix Applied:**

1. Backend now **NEVER returns phishing/suspicious** until analysis is 100% complete
2. Extension polls for updates when verdict is `pending`
3. Extension only shows popup when `analysis_complete === true`
4. All results are double-checked before returning

## Why Emails Weren't Being Quarantined

**Previous Issue (Now Fixed):**

1. Phishing emails had action `delete`
2. `quarantine_email()` set status to `deleted` for delete actions
3. Quarantine list only showed `status='pending'`
4. Phishing emails were quarantined but not visible

**Fix Applied:**

1. All quarantined emails now have `status='pending'`
2. Email deletion happens via `execute_email_action()` (separate from quarantine)
3. Quarantine list shows all pending emails (including phishing)

## Database Tables

### `emails`
- Stores all processed emails
- Fields: message_id, subject, sender, body_html, auth_score, is_suspicious

### `email_auth_results`
- Stores SPF/DKIM/DMARC results
- Linked to `emails` via foreign key

### `url_analyses`
- Stores URL analysis results
- Fields: url, google_safebrowsing, urlhaus_status, urlscan_status, final_verdict
- Linked to `emails` via foreign key

### `classification_results`
- Stores final classification
- Fields: rule_engine_verdict, final_action, reason, confidence_score
- Linked to `emails` via foreign key

### `quarantined_emails`
- Stores quarantined emails
- Fields: email (FK), user (FK), reason, status, created_at
- Status: `pending`, `released`, `deleted`
- **All new quarantines have status `pending`**

## Key Points

1. **All emails are processed automatically** via webhooks - you don't need to open them
2. **Analysis is multi-stage**: Authentication → URL Analysis → Classification
3. **Classification only runs when analysis is complete** - no premature results
4. **Extension polls for updates** when analysis is pending
5. **All quarantined emails show in list** regardless of action (delete/quarantine)
6. **Confidence scores are calculated** based on all analysis factors

## Troubleshooting

**Q: Why do I see many emails in dashboard but I haven't opened them?**
A: Webhooks automatically process all incoming emails in the background.

**Q: Why did phishing popup appear then change to safe?**
A: This is now fixed - backend never returns phishing until analysis is 100% complete.

**Q: Why aren't phishing emails in quarantine?**
A: This is now fixed - all quarantined emails (including phishing) have status `pending` and show in the list.

**Q: How long does analysis take?**
A: 
- Authentication: Instant
- URL analysis: 5-30 seconds (depends on URLScan.io)
- Classification: Runs immediately after URL analysis completes

