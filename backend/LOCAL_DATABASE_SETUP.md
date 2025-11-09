# Local PostgreSQL Database Setup Guide

This guide explains how to configure the Django backend to use a local PostgreSQL database instead of Supabase.

## Prerequisites

1. **Install PostgreSQL** on your machine:
   - Windows: Download from https://www.postgresql.org/download/windows/
   - macOS: `brew install postgresql` or download from postgresql.org
   - Linux: `sudo apt-get install postgresql postgresql-contrib` (Ubuntu/Debian)

2. **Start PostgreSQL service**:
   - Windows: PostgreSQL should start automatically as a service
   - macOS: `brew services start postgresql`
   - Linux: `sudo systemctl start postgresql`

## Step 1: Create a Database

Open PostgreSQL command line (psql) or use a GUI tool like pgAdmin:

```bash
# Connect to PostgreSQL (default user is usually 'postgres')
psql -U postgres

# Create a new database
CREATE DATABASE spam_shield_db;

# Create a user (optional, or use existing 'postgres' user)
CREATE USER spam_shield_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE spam_shield_db TO spam_shield_user;

# Exit psql
\q
```

## Step 2: Update .env File

In your `backend/` directory, update the `.env` file:

```env
# Local PostgreSQL Database
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/spam_shield_db

# Or if you created a custom user:
# DATABASE_URL=postgresql://spam_shield_user:your_secure_password@localhost:5432/spam_shield_db
```

**Important Notes:**
- Replace `your_password` with your actual PostgreSQL password
- Replace `spam_shield_db` with your database name
- Default port is `5432`
- If your password contains special characters, URL-encode them:
  - `@` → `%40`
  - `#` → `%23`
  - `$` → `%24`
  - etc.

## Step 3: Run Migrations

After updating the `.env` file, run Django migrations:

```bash
cd backend/spam_shield
python manage.py migrate
```

This will create all necessary tables in your local database.

## Step 4: Create Superuser (Optional)

Create a Django admin superuser:

```bash
python manage.py createsuperuser
```

## Step 5: Test the Connection

Start the Django server:

```bash
python manage.py runserver
```

If it starts without errors, your local database connection is working!

## Troubleshooting

### Connection Refused Error
- Make sure PostgreSQL service is running
- Check if port 5432 is correct
- Verify the host is `localhost` (not `127.0.0.1`)

### Authentication Failed
- Verify the username and password in your `.env` file
- Make sure the user has proper permissions on the database

### Database Does Not Exist
- Create the database first using `CREATE DATABASE spam_shield_db;`
- Or update `DATABASE_URL` to use an existing database

### Module Not Found: psycopg2
- Install it: `pip install psycopg2-binary`
- Or if using Pipenv: `pipenv install psycopg2-binary`

## Important Notes

⚠️ **Supabase is still required for data storage!**

Even though you're using a local database for Django, the application still uses Supabase for:
- Storing email data (emails, email_auth_results, url_analysis, etc.)
- Storing connected account information
- System logs

The `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in your `.env` file are still needed for database operations.

**Note:** User authentication is now handled by Django allauth, not Supabase. Users authenticate via Google or Microsoft OAuth through django-allauth.

## Switching Back to Supabase

To switch back to Supabase database, simply update `DATABASE_URL` in your `.env`:

```env
DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

