# SOS Feature Setup Guide

## Overview
The SOS (Emergency Alert) feature allows users to trigger emergency alerts that send SMS notifications to their emergency contacts with their location.

## Current Status
✅ **Development Mode Active**: The SOS feature now works WITHOUT Redis/Celery running!
- If Redis is available: Tasks run asynchronously via Celery (recommended for production)
- If Redis is unavailable: Tasks run synchronously (good for development/testing)

⚠️ **Twilio Configuration Required**: To send actual SMS alerts, you need:
1. A valid Twilio phone number (not your personal number)
2. Emergency contact numbers verified (if using trial account)
3. See `TWILIO_SETUP_GUIDE.md` for detailed instructions

✅ **Current Protection**: System now prevents "same number" error by skipping contacts that match the Twilio sender number

## How It Works

### 1. User Setup
Users need to add emergency contacts via the API:
```bash
POST /api/emergency/contacts/
{
  "name": "John Doe",
  "relationship": "Spouse",
  "phone_number": "+1234567890",
  "email": "john@example.com"
}
```

### 2. Trigger SOS
When a user triggers an SOS alert:
```bash
POST /api/emergency/trigger_sos/
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "message": "I need help!" (optional)
}
```

### 3. Alert Processing
The system will:
1. Create an `EmergencyAlert` record
2. Attempt to send SMS to all emergency contacts via Twilio
3. Log delivery status for each contact
4. Include a Google Maps link with the user's location

## Production Setup (Recommended)

### 1. Install and Start Redis
```bash
# macOS (with Homebrew)
brew install redis
brew services start redis

# Or run manually
redis-server

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis
```

### 2. Start Celery Worker
```bash
cd VitaNips-Backend-Dev
source env/bin/activate
celery -A vitanips worker -l info
```

### 3. Start Celery Beat (for scheduled tasks)
```bash
celery -A vitanips beat -l info
```

### 4. Configure Twilio (Required for SMS)
Set environment variables in your `.env` file or system:
```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

**Note:** Without Twilio credentials, alerts will be logged but SMS won't be sent.

## Development Mode (Current)

For testing without Redis:
1. ✅ Server is running
2. ✅ SOS endpoint works synchronously
3. ⚠️ SMS won't send without Twilio credentials (logs only)
4. ⚠️ Scheduled tasks (appointment/medication reminders) won't run

## Testing the SOS Feature

### 1. Create a Test User
Use any of the mock users created (password: `password123`):
- user0_christianperez@example.com
- user1_vparker@example.com
- etc.

### 2. Add Emergency Contacts
```bash
curl -X POST http://localhost:8000/api/emergency/contacts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Emergency Contact",
    "relationship": "Friend",
    "phone_number": "+1234567890",
    "email": "contact@example.com"
  }'
```

### 3. Trigger SOS
```bash
curl -X POST http://localhost:8000/api/emergency/trigger_sos/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.7128,
    "longitude": -74.0060,
    "message": "Testing SOS"
  }'
```

### 4. Check Alert Status
```bash
curl http://localhost:8000/api/emergency/alerts/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### Redis Connection Error
**Symptom:** `Error 61 connecting to localhost:6379. Connection refused.`
**Solution:** ✅ Now handled automatically! Task runs synchronously without Redis.

### No SMS Sent
**Symptom:** Alert created but no SMS received
**Possible causes:**
1. Twilio credentials not configured → Check environment variables
2. Phone numbers not in E.164 format → Use format: +[country code][number]
3. Twilio account not verified → Verify phone numbers in Twilio console

### Task Not Running
**Symptom:** SOS triggered but nothing happens
**Solution:** Check server logs for errors. Task now runs synchronously if Redis is unavailable.

## API Endpoints

### Emergency Contacts
- `GET /api/emergency/contacts/` - List user's emergency contacts
- `POST /api/emergency/contacts/` - Add emergency contact
- `GET /api/emergency/contacts/{id}/` - Get contact details
- `PUT /api/emergency/contacts/{id}/` - Update contact
- `DELETE /api/emergency/contacts/{id}/` - Delete contact

### Emergency Services
- `GET /api/emergency/services/` - List emergency services (hospitals, police, etc.)
- Query params: `?lat=40.7128&lon=-74.0060&radius=5&service_type=hospital`

### Emergency Alerts
- `GET /api/emergency/alerts/` - List user's SOS alerts
- `POST /api/emergency/trigger_sos/` - Trigger SOS alert
- `GET /api/emergency/alerts/{id}/` - Get alert details
- `PUT /api/emergency/alerts/{id}/` - Update alert (e.g., mark resolved)

## Next Steps

1. ✅ Mock data populated
2. ✅ SOS works without Redis (development mode)
3. 🔄 Test SOS feature from frontend
4. ⏭️ Continue with next feature (Telehealth)

For production deployment:
- Set up Redis and Celery workers
- Configure Twilio credentials
- Test SMS delivery
- Set up monitoring for failed alerts
