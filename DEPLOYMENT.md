# VitaNips Backend - Fly.io Deployment Guide

This guide will help you deploy the VitaNips backend to Fly.io.

## Prerequisites

1. Install the [Fly CLI](https://fly.io/docs/getting-started/installing-flyctl/)
2. Sign up for a [Fly.io account](https://fly.io/app/sign-up)
3. Login to Fly.io: `fly auth login`

## Initial Setup

### 1. Create a Fly.io App

```bash
cd VitaNips-Backend-Dev
fly launch
```

When prompted:
- **App name**: Choose a name (e.g., `vitanips-backend`) or let Fly.io generate one
- **Region**: Choose the closest region to your users (e.g., `iad` for US East)
- **Postgres**: Yes, create a Postgres database
- **Redis**: Yes, create a Redis instance (needed for Celery and Channels)

### 2. Set Environment Variables

Set all required environment variables using `fly secrets set`:

```bash
# Django Settings
fly secrets set SECRET_KEY="your-secret-key-here"
fly secrets set DEBUG="False"
fly secrets set ALLOWED_HOSTS="your-app-name.fly.dev,*.fly.dev"
fly secrets set DJANGO_ENV="production"

# Database (automatically set by Fly.io Postgres, but verify)
# DATABASE_URL is automatically set by Fly.io

# CORS Settings
fly secrets set CORS_ALLOWED_ORIGINS="https://your-frontend-domain.com,https://your-frontend-domain.vercel.app"

# CSRF Trusted Origins
fly secrets set CSRF_TRUSTED_ORIGINS="https://your-app-name.fly.dev,https://your-frontend-domain.com"

# Frontend URL
fly secrets set FRONTEND_URL="https://your-frontend-domain.com"

# Payment Gateway (Flutterwave)
fly secrets set FLUTTERWAVE_SECRET_KEY="your-flutterwave-secret-key"
fly secrets set FLUTTERWAVE_PUBLIC_KEY="your-flutterwave-public-key"

# Celery Configuration
fly secrets set CELERY_BROKER_URL="redis://your-redis-instance.fly.dev:6379/0"
fly secrets set CELERY_RESULT_BACKEND="redis://your-redis-instance.fly.dev:6379/0"

# Redis for Channels (WebSockets)
fly secrets set REDIS_HOST="your-redis-instance.fly.dev"
fly secrets set REDIS_PORT="6379"

# Email Configuration (choose one)
# Option 1: SMTP
fly secrets set EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
fly secrets set EMAIL_HOST="smtp.gmail.com"
fly secrets set EMAIL_PORT="587"
fly secrets set EMAIL_USE_TLS="True"
fly secrets set EMAIL_HOST_USER="your-email@gmail.com"
fly secrets set EMAIL_HOST_PASSWORD="your-app-password"

# Option 2: SendGrid
# fly secrets set EMAIL_BACKEND="anymail.backends.sendgrid.EmailBackend"
# fly secrets set SENDGRID_API_KEY="your-sendgrid-api-key"

# Twilio (for SMS and video calls)
fly secrets set TWILIO_ACCOUNT_SID="your-twilio-account-sid"
fly secrets set TWILIO_AUTH_TOKEN="your-twilio-auth-token"
fly secrets set TWILIO_PHONE_NUMBER="your-twilio-phone-number"
fly secrets set TWILIO_API_KEY_SID="your-twilio-api-key-sid"
fly secrets set TWILIO_API_KEY_SECRET="your-twilio-api-key-secret"

# AWS S3 (for media storage - optional)
fly secrets set AWS_ACCESS_KEY_ID="your-aws-access-key"
fly secrets set AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
fly secrets set AWS_STORAGE_BUCKET_NAME="your-bucket-name"
fly secrets set AWS_S3_REGION_NAME="us-east-1"

# Firebase (for push notifications)
# Upload firebase-service-account.json to Fly.io volumes or use environment variables
fly secrets set FIREBASE_SERVICE_ACCOUNT_KEY="firebase-service-account.json"
```

### 3. Attach Postgres Database

If you created a Postgres database during `fly launch`, it should already be attached. If not:

```bash
fly postgres attach --app your-app-name
```

### 4. Attach Redis Instance

If you created a Redis instance during `fly launch`, it should already be configured. Verify the connection:

```bash
fly redis connect
```

### 5. Upload Firebase Service Account Key

You have two options:

**Option A: Using Fly.io Volumes (Recommended)**
```bash
# Create a volume
fly volumes create firebase_data --size 1 --region iad

# Mount it in fly.toml (add to [[mounts]] section)
```

**Option B: Base64 Encode and Store as Secret**
```bash
# Encode the file
cat firebase-service-account.json | base64 | fly secrets set FIREBASE_SERVICE_ACCOUNT_JSON="$(cat)"
```

Then update `settings.py` to decode it if using Option B.

### 6. Deploy

```bash
fly deploy
```

## Post-Deployment

### 1. Run Migrations

Migrations should run automatically via `start.sh`, but you can also run them manually:

```bash
fly ssh console -C "python manage.py migrate"
```

### 2. Create Superuser

```bash
fly ssh console -C "python manage.py createsuperuser"
```

### 3. Verify Health Check

```bash
curl https://your-app-name.fly.dev/health/
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "debug": false
}
```

## Scaling

### Scale App Instances

```bash
# Scale to 2 instances
fly scale count app=2

# Scale with more memory
fly scale vm shared-cpu-1x --memory 1024
```

### Scale Celery Workers

```bash
# Scale Celery workers
fly scale count celery=2
```

## Monitoring

### View Logs

```bash
# All logs
fly logs

# App logs only
fly logs --app your-app-name

# Celery logs
fly logs --app your-app-name --process celery
```

### Check App Status

```bash
fly status
```

### SSH into Container

```bash
fly ssh console
```

## Troubleshooting

### Database Connection Issues

1. Verify DATABASE_URL is set: `fly secrets list`
2. Check Postgres is running: `fly postgres list`
3. Test connection: `fly ssh console -C "python manage.py dbshell"`

### Redis Connection Issues

1. Verify Redis is running: `fly redis list`
2. Check REDIS_HOST and REDIS_PORT secrets
3. Test connection: `fly redis connect`

### Static Files Not Loading

1. Ensure `collectstatic` runs during deployment
2. Check WhiteNoise is configured in `settings.py`
3. Verify STATIC_ROOT is set correctly

### GDAL/GEOS Issues

The Dockerfile includes GDAL/GEOS libraries. If you encounter issues:

1. Verify the libraries are installed: `fly ssh console -C "gdalinfo --version"`
2. Check environment variables in `settings.py`

## Environment-Specific Configuration

The `fly.toml` file is configured for:
- **App process**: Main Django application (Daphne ASGI server)
- **Celery process**: Background task worker
- **Celery Beat process**: Scheduled task scheduler

Each process runs in separate VMs for better isolation and scaling.

## Health Checks

The app includes a health check endpoint at `/health/` that:
- Checks database connectivity
- Returns application status
- Used by Fly.io for automatic health monitoring

## Additional Resources

- [Fly.io Django Guide](https://fly.io/docs/django/)
- [Fly.io Postgres](https://fly.io/docs/postgres/)
- [Fly.io Redis](https://fly.io/docs/redis/)
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/)

