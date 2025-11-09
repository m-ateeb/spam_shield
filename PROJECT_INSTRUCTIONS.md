NOTE: envs are given in the project

⚙️ Setup Instructions
1️⃣ Clone the Repository
    git clone https://github.com/yourusername/spam-shield-backend.git
    cd spam-shield-backend

2️⃣ Create and Activate a Virtual Environment
    python -m venv venv
    source venv/bin/activate   # On macOS/Linux
    venv\Scripts\activate      # On Windows

3️⃣ Install Dependencies
    pip install -r requirements.txt

4️⃣ Configure Environment Variables

Create a .env file in the project root with the following values:
[
    # Django
    SECRET_KEY=your-secret-key
    DEBUG=True
    ALLOWED_HOSTS=*

    # Supabase (Database only - not for authentication)
    SUPABASE_URL=https://xyzcompany.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
    
    # Frontend URL (for OAuth redirects)
    FRONTEND_URL=http://localhost:5173

    # Database (PostgreSQL)
    # For Supabase (cloud):
    # DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
    # For Local PostgreSQL:
    DATABASE_URL=postgresql://username:password@localhost:5432/database_name
    # Example: DATABASE_URL=postgresql://postgres:mysecretpassword@localhost:5432/spam_shield_db

    # Redis (for Celery)
    REDIS_URL=rediss://default:<your-upstash-redis-url>

    # OAuth Credentials (for user authentication via django-allauth)
    GOOGLE_CLIENT_ID=your-google-client-id
    GOOGLE_CLIENT_SECRET=your-google-client-secret
    GOOGLE_PROJECT_ID=your-google-project-id
    MICROSOFT_CLIENT_ID=your-microsoft-client-id
    MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
    
    # IMPORTANT: Configure these redirect URIs in your OAuth provider consoles:
    # Google: http://localhost:8000/accounts/google/login/callback/
    # Microsoft: http://localhost:8000/accounts/microsoft/login/callback/
    # See OAUTH_SETUP.md for detailed instructions

    # Encryption
    FERNET_KEY=your-generated-fernet-key

    # Webhook
    WEBHOOK_URL=https://your-deployment-url/webhook/

    # Optional Config
    EMAIL_BATCH_SIZE=10
]


💡 You can generate a FERNET key by running this command in Terminal:
    from cryptography.fernet import Fernet
    print(Fernet.generate_key().decode())

5️⃣ Run Database Migrations
    python manage.py migrate
    
    # Create a Site object for django-allauth (required)
    python manage.py shell
    >>> from django.contrib.sites.models import Site
    >>> site = Site.objects.get(id=1)
    >>> site.domain = 'localhost:8000'  # or your domain
    >>> site.name = 'SpamShield'
    >>> site.save()
    >>> exit()

6️⃣ Start the Django Development Server
    python manage.py runserver


Now the backend should be available at:
    http://127.0.0.1:8000/

7️⃣ Start Celery Worker
    In a new terminal window (with the same virtual environment activated):
    celery -A spam_shield worker --loglevel=info

You should see tasks like:

Task spam_shield.email_connector.tasks.process_incoming_email started...

🧠 Email Processing Pipeline
    1️⃣	tasks.py	Fetches new emails via Gmail/Outlook APIs
    2️⃣	email_validator.py	Runs SPF, DKIM, and DMARC checks
    3️⃣	url_reputation.py	Scans URLs for phishing or malicious intent
    4️⃣	decision_engine.py	Applies rule-based classification
    5️⃣	views.py	Exposes results through dashboard APIs

All results are stored in Supabase tables:
    emails

    email_auth_results

    url_analysis

    classification_results

    quarantine

🧾 Available API Endpoints (Key Routes)
    # User Authentication (django-allauth)
    /accounts/google/login/	GET	Redirect to Google OAuth login
    /accounts/microsoft/login/	GET	Redirect to Microsoft OAuth login
    /api/auth/token/	GET	Get API token for authenticated user
    /api/auth/user/	GET	Get current user information
    /api/auth/callback/	GET	OAuth callback handler (redirects to frontend)
    
    # Email Account Connection
    /oauth/google/	GET	Redirect to Google OAuth (for Gmail connection)
    /oauth/google/callback/	GET	Handles Google OAuth callback
    /oauth/microsoft/	GET	Redirect to Microsoft OAuth (for Outlook connection)
    /oauth/microsoft/callback/	GET	Handles Microsoft OAuth callback
    /webhook/	POST	Receives new email notifications
    /dashboard/stats/	GET	Returns summary stats for user dashboard
    /dashboard/quarantine/	GET	Fetch quarantined emails
    /dashboard/quarantine/action/	POST	Restore or delete quarantined emails

🧪 Testing the Setup
    Once the backend and Celery are running:
    1. First, authenticate as a user by visiting /accounts/google/login/ or /accounts/microsoft/login/
    2. After authentication, you'll be redirected to the frontend with an API token
    3. Use the API token to connect your email accounts via /oauth/google/ or /oauth/microsoft/

    Send a test email to your connected inbox.
    Backend will:

    Fetch the email automatically.

    Run SPF/DKIM/DMARC and URL checks.

    Store results in Supabase.

    Check logs for:

    [INFO] Email classified as suspicious — moved to quarantine.

Make sure environment variables are configured in the platform dashboard before deployment.


## Frontend Setup (Vite + React)

NOTE: Frontend is incomplete yet as it is in our assignment 4

These instructions cover running the React frontend (located in `frontend/`) for development and production builds.

Prerequisites
- Node.js 18+ (LTS recommended)
- npm or pnpm (pnpm recommended but optional)

1️⃣ Install dependencies

Windows PowerShell:
    cd frontend
    npm install


2️⃣ Environment variables

The frontend uses Vite. Environment variables should be prefixed with `VITE_` to be available in client code.
Create a `.env` file in `frontend/` with the values below:

    # Backend API URL
    VITE_API_URL=http://127.0.0.1:8000

    # Extension redirect (optional - only if using browser extension)
    VITE_EXTENSION_REDIRECT_URI=chrome-extension://<extension-id>/oauth/callback

**Important Notes:**
- `VITE_API_URL` should point to your running backend during development
- **Remove any `VITE_SUPABASE_URL` or `VITE_SUPABASE_ANON_KEY`** - Supabase is no longer used for authentication
- Authentication is now handled by Django allauth with email/password and OAuth (Google/Microsoft)
- If testing the extension, set `VITE_EXTENSION_REDIRECT_URI` to the extension's redirect URI

3️⃣ Run the dev server

Windows PowerShell:
    npm run dev

This starts Vite (hot module reload). The console will show the local URL (usually `http://localhost:5173`).



5️⃣ Useful commands

- Start dev server: `npm run dev`
s
6️⃣ Running frontend together with backend and Celery

- Start the backend (`python manage.py runserver`) and Celery worker as described above.
- In another terminal, start the frontend dev server (`npm run dev`).
- Open the frontend URL in your browser and sign in via the frontend OAuth flows which will call the backend endpoints.

7️⃣ Testing

- The frontend includes unit/integration tests if available in `package.json` (e.g., `npm test` or `npm run test`). Run them from `frontend/`.


## Browser Extension Setup (in `extension/`)

NOTE: Extension is incomplete yet as it is in our assignment 4


Prerequisites
- A Chromium-based browser (Chrome, Edge) or Firefox for extension testing
- For Chromium dev: `chrome://extensions/` (enable Developer mode)

1️⃣ Structure overview

- `extension/manifest.json` — manifest and permissions
- `extension/background/service-worker.js` — background worker logic
- `extension/content/gmail.js` `extension/content/outlook.js` — content scripts injected into pages
- `extension/popup/` and `extension/options/` — UI for extension
- `extension/assets/` — icons and static assets

2️⃣ Running in development (load unpacked)

Chromium (Chrome/Edge):
    1. Open `chrome://extensions/` in the browser.
    2. Enable "Developer mode" (top-right).
    3. Click "Load unpacked" and select the `extension/` directory from this repo.
    4. open your gmail to view extension 


## Quick checklist — dev session

- [ ] Configure backend `.env` and start Django server
- [ ] Start Celery worker
- [ ] Configure `frontend/.env` and run `npm run dev`
- [ ] Load `extension/` unpacked in browser and test flows




Completion: follow the backend, frontend, and extension steps above to run the full system locally and test end-to-end flows.