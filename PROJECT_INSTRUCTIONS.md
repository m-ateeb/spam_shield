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

    # Supabase
    SUPABASE_URL=https://xyzcompany.supabase.co
    SUPABASE_KEY=your-service-role-key
    SUPABASE_JWT_SECRET=your-supabase-jwt-secret

    # Database (PostgreSQL)
    DATABASE_URL=postgresql://username:password@host:port/database

    # Redis (for Celery)
    REDIS_URL=rediss://default:<your-upstash-redis-url>

    # OAuth Credentials
    GOOGLE_CLIENT_ID=your-google-client-id
    GOOGLE_CLIENT_SECRET=your-google-client-secret
    MICROSOFT_CLIENT_ID=your-microsoft-client-id
    MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
    REDIRECT_URI=https://your-frontend-url/oauth/callback

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
    /auth/verify/	POST	Verifies JWT token
    /oauth/google/login/	GET	Redirect to Google login
    /oauth/google/callback/	GET	Handles Google OAuth callback
    /oauth/outlook/login/	GET	Redirect to Microsoft login
    /oauth/outlook/callback/	GET	Handles Outlook OAuth callback
    /webhook/	POST	Receives new email notifications
    /dashboard/stats/	GET	Returns summary stats for user dashboard
    /dashboard/quarantine/	GET	Fetch quarantined emails
    /dashboard/quarantine/action/	POST	Restore or delete quarantined emails

🧪 Testing the Setup
    Once the backend and Celery are running:
    Go to /oauth/google/login/ or /oauth/outlook/login/ to connect your email.

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
Create a `.env` file in `frontend/` with the values below (example keys — do NOT commit secrets):

    VITE_SUPABASE_URL=https://xyzcompany.supabase.co
    VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
    VITE_API_URL=http://127.0.0.1:8000
    VITE_EXTENSION_REDIRECT_URI=chrome-extension://<extension-id>/oauth/callback

Notes:
- Use the backend `SUPABASE_URL` and a client-safe anon key for the frontend.
- `VITE_API_URL` should point to your running backend during development.
- If testing the extension, set `VITE_EXTENSION_REDIRECT_URI` to the extension's redirect URI or the dev extension id once loaded.

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