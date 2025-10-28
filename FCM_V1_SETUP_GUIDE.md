# Firebase Cloud Messaging (FCM) Setup Guide - HTTP v1 API

## 🔔 Overview

Firebase has deprecated the legacy Cloud Messaging API. This guide shows you how to set up push notifications using the modern **FCM HTTP v1 API**.

## ✅ What You Need

- Firebase project: **vitanips-800cd** ✓ (You already have this)
- Service Account JSON key file (We'll get this now)

---

## 📥 Step-by-Step: Get Service Account Key

### 1. Open Firebase Console

Go to: https://console.firebase.google.com/

### 2. Select Your Project

Click on **vitanips-800cd**

### 3. Navigate to Service Accounts

1. Click the **⚙️ gear icon** (Settings) next to "Project Overview"
2. Select **"Project settings"**
3. Click on the **"Service accounts"** tab

### 4. Generate Private Key

1. Scroll down to **"Firebase Admin SDK"** section
2. Click the **"Generate new private key"** button
3. A popup will appear - click **"Generate key"**
4. A JSON file will download automatically (e.g., `vitanips-800cd-firebase-adminsdk-xxxxx.json`)

### 5. Rename and Move the File

```bash
# Rename the downloaded file
mv ~/Downloads/vitanips-800cd-firebase-adminsdk-*.json firebase-service-account.json

# Move it to your backend project root
mv firebase-service-account.json /Users/rpublc/Documents/myprojects/VitaNips/VitaNips-Backend-Dev/
```

### 6. Secure the File

```bash
# Make sure it's not tracked by git
echo "firebase-service-account.json" >> .gitignore

# Set proper permissions (read-only for owner)
chmod 600 firebase-service-account.json
```

---

## 📦 Install Required Package

```bash
cd VitaNips-Backend-Dev
source env/bin/activate  # Activate your virtual environment

# Install firebase-admin for FCM v1 API support
pip install firebase-admin==6.6.0

# Or install all requirements
pip install -r requirements.txt
```

---

## ✅ Verify Installation

```bash
python manage.py shell
```

```python
# In Python shell:
from django.conf import settings
from pathlib import Path

# Check if service account file exists
key_path = settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH
print(f"Service account key exists: {key_path.exists()}")
print(f"Key path: {key_path}")

# Test Firebase initialization
from vitanips.core.push_notifications import initialize_firebase
result = initialize_firebase()
print(f"Firebase initialized: {result}")
```

Expected output:
```
Service account key exists: True
Key path: /Users/rpublc/Documents/myprojects/VitaNips/VitaNips-Backend-Dev/firebase-service-account.json
✓ Firebase Admin SDK initialized successfully
Firebase initialized: True
```

---

## 🧪 Test Push Notifications

### Test Script

```python
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from vitanips.core.push_notifications import send_fcm_notification

User = get_user_model()
user = User.objects.first()  # Get a test user

# Send a test notification
result = send_fcm_notification(
    user=user,
    title="🏥 Test from VitaNips",
    body="If you see this, push notifications are working!",
    data={
        "type": "test",
        "url": "/dashboard"
    }
)

print(f"Success: {result['success']}, Failure: {result['failure']}")
```

### Important Notes

1. **User must have registered a device token first**
   - The frontend must call `/api/notifications/devices/register/` with their FCM token
   - This happens automatically when user grants notification permissions

2. **Check registered devices:**
   ```python
   from push_notifications.models import GCMDevice
   print(f"Total FCM devices: {GCMDevice.objects.count()}")
   print(f"Devices for user {user.id}: {GCMDevice.objects.filter(user=user, active=True).count()}")
   ```

3. **If no devices registered:**
   - Open the frontend app in browser
   - Grant notification permissions when prompted
   - Check browser console for "Device registered successfully"

---

## 🔄 How It Works

### Backend Flow

1. **Initialization** (on Django startup):
   - Checks if `firebase-service-account.json` exists
   - Initializes Firebase Admin SDK
   - Logs configuration status

2. **Sending Notifications**:
   ```python
   # From Celery tasks or views
   from vitanips.core.push_notifications import send_notification_to_user
   
   send_notification_to_user(
       user=user,
       notification_type='appointment_reminder',
       title='Appointment Tomorrow',
       body='Your appointment with Dr. Smith is tomorrow at 10 AM',
       url='/appointments/123'
   )
   ```

3. **Automatic Fallback**:
   - Tries FCM v1 API first (modern)
   - Falls back to legacy API if service account not available
   - Logs which method is being used

### Frontend Flow

1. **User grants permission** (src/utils/pushNotifications.ts)
2. **Gets FCM token** from Firebase SDK
3. **Registers token** with backend via API
4. **Backend stores** token in `GCMDevice` model
5. **Receives notifications** automatically

---

## 🔧 Troubleshooting

### Service Account File Not Found

```bash
# Check if file exists
ls -la firebase-service-account.json

# Check .env configuration
grep FIREBASE_SERVICE_ACCOUNT_KEY .env
```

### Firebase Admin Import Error

```bash
# Make sure package is installed
pip list | grep firebase-admin

# Reinstall if needed
pip install --upgrade firebase-admin
```

### No Devices Registered

```python
from push_notifications.models import GCMDevice
devices = GCMDevice.objects.all()
for device in devices:
    print(f"User: {device.user.email}, Active: {device.active}, Token: {device.registration_id[:20]}...")
```

### Check Logs

```bash
# View Django logs
tail -f logs/app.log | grep -i firebase

# Check for initialization message
grep "Firebase Admin SDK initialized" logs/app.log
```

---

## 🎯 Integration with Existing Code

Your existing task code will continue to work! The new module provides:

### Option 1: Keep Existing Code (Legacy API)

```python
# Your current code in tasks.py still works
fcm_devices.send_message(title=title, body=body, data=data)
```

### Option 2: Use New Helper (Recommended)

```python
# Updated approach using the helper
from vitanips.core.push_notifications import send_fcm_notification

result = send_fcm_notification(
    user=user,
    title=title,
    body=body,
    data=data
)
```

### Benefits of New Helper

- ✅ Automatically uses FCM v1 API
- ✅ Falls back to legacy if needed
- ✅ Better error handling
- ✅ Handles device cleanup (inactive tokens)
- ✅ Rich notifications with images
- ✅ Web push specific options

---

## 📊 Comparison: Legacy vs New API

| Feature | Legacy API | FCM v1 API |
|---------|-----------|------------|
| Status | ❌ Deprecated (June 2024) | ✅ Current |
| Auth | Server Key | Service Account JSON |
| Security | Less secure | More secure (OAuth 2.0) |
| Features | Basic | Rich (images, actions, etc.) |
| Rate Limit | Lower | Higher |
| Documentation | Outdated | Up-to-date |

---

## 🚀 Production Checklist

- [ ] Download service account JSON from Firebase
- [ ] Save as `firebase-service-account.json` in project root
- [ ] Add to `.gitignore`
- [ ] Set file permissions: `chmod 600 firebase-service-account.json`
- [ ] Install: `pip install firebase-admin`
- [ ] Test initialization: Run verification script
- [ ] Test sending: Send test notification
- [ ] Update tasks (optional): Use new helper functions
- [ ] Monitor logs: Check for initialization success
- [ ] Deploy: Include service account file in deployment
- [ ] Environment: Set proper permissions on server

---

## 🔒 Security Best Practices

### Development

```bash
# Never commit the service account file
echo "firebase-service-account.json" >> .gitignore
git rm --cached firebase-service-account.json  # If already committed
```

### Production

**Option 1: Environment Variable (Recommended for cloud)**

```python
# Store JSON content as environment variable
import os
import json

FIREBASE_SERVICE_ACCOUNT = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON'))
```

**Option 2: Secrets Manager**

- AWS Secrets Manager
- Google Cloud Secret Manager
- Azure Key Vault
- HashiCorp Vault

**Option 3: File on Server**

```bash
# On production server
sudo mkdir -p /etc/vitanips/secrets/
sudo cp firebase-service-account.json /etc/vitanips/secrets/
sudo chmod 600 /etc/vitanips/secrets/firebase-service-account.json
sudo chown www-data:www-data /etc/vitanips/secrets/firebase-service-account.json
```

Update `.env`:
```env
FIREBASE_SERVICE_ACCOUNT_KEY=/etc/vitanips/secrets/firebase-service-account.json
```

---

## 📞 Support Resources

- **Firebase Documentation**: https://firebase.google.com/docs/cloud-messaging
- **Admin SDK Reference**: https://firebase.google.com/docs/reference/admin/python
- **Migration Guide**: https://firebase.google.com/docs/cloud-messaging/migrate-v1
- **Service Accounts**: https://firebase.google.com/docs/admin/setup#initialize-sdk

---

## ✅ Next Steps

1. **Get Service Account Key** - Follow steps above
2. **Test Push Notifications** - Use test script
3. **Update Your Tasks** (Optional) - Use new helper functions
4. **Monitor** - Check logs for successful initialization
5. **Deploy** - Ensure service account file is properly deployed

**Need help?** Check `logs/app.log` for detailed error messages and initialization status.
