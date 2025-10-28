# Twilio Setup Guide for VitaNips

## Overview
VitaNips uses Twilio for two main features:
1. **SMS Alerts** - Send SOS emergency notifications to emergency contacts
2. **Video Calls** - Enable doctor-patient virtual appointments

## Step-by-Step Setup

### 1. Create a Twilio Account
1. Go to https://www.twilio.com/try-twilio
2. Sign up for a free trial account
3. Verify your email and phone number
4. You'll get free trial credits (~$15) to test with

### 2. Get SMS Credentials (For Emergency SOS Alerts)

#### A. Get Account SID and Auth Token
1. Login to Twilio Console: https://console.twilio.com/
2. On the Dashboard, you'll see:
   - **Account SID** - Copy this value
   - **Auth Token** - Click "Show" to reveal, then copy

#### B. Purchase a Phone Number
1. Navigate to **Phone Numbers** → **Manage** → **Buy a number**
2. Select your country (e.g., United States)
3. Check the **SMS** capability box
4. Click **Search**
5. Choose a number and click **Buy**
6. Copy the phone number (format: `+1234567890`)

**Note:** During trial, you can only send SMS to verified phone numbers. To send to any number, you'll need to upgrade your account.

### 3. Get Video API Credentials (For Virtual Appointments)

1. Go to **Account** → **API keys & tokens**
2. Click **Create API key**
3. Configure:
   - **Friendly name**: `VitaNips Video API`
   - **Key type**: Standard
4. Click **Create API Key**
5. **IMPORTANT:** Copy these immediately (shown only once):
   - **SID** (starts with `SK...`)
   - **Secret** (long random string)

### 4. Configure Your .env File

Open `/Users/rpublc/Documents/myprojects/VitaNips/VitaNips-Backend-Dev/.env` and update:

```bash
# Twilio SMS Configuration (for SOS alerts)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_32_character_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# Twilio Video Configuration (for doctor appointments)
TWILIO_API_KEY_SID=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_KEY_SECRET=your_api_key_secret_here
```

### 5. Restart Your Django Server

```bash
cd /Users/rpublc/Documents/myprojects/VitaNips/VitaNips-Backend-Dev
source env/bin/activate
python manage.py runserver
```

You should no longer see the warning:
> "WARNING: Twilio credentials not found in environment variables."

## Testing

### Test SMS Functionality
1. Create a user and add emergency contacts
2. Trigger an SOS alert
3. Emergency contacts should receive SMS with location

**Trial Limitations:**
- Can only send to verified numbers
- Messages include "Sent from a Twilio Trial Account"
- Limited to ~$15 credit

### Test Video Functionality
1. Create a doctor and patient account
2. Book a virtual appointment
3. Join the appointment - you'll get a Twilio Video token
4. Frontend should connect to Twilio Video room

## Production Deployment

When deploying to production:

1. **Upgrade Twilio Account**
   - Go to https://console.twilio.com/billing
   - Add payment method
   - Remove trial limitations

2. **Verify Phone Numbers**
   - Add your emergency contact numbers to verified list
   - Or upgrade to send to any number

3. **Set Environment Variables**
   - Set Twilio credentials in production environment
   - Never commit `.env` to version control

4. **Monitor Usage**
   - Check Twilio Console for usage stats
   - Set up billing alerts

## Pricing

**SMS:** ~$0.0079 per message (US)
**Video:** ~$0.0015/min/participant

Free trial: $15 credit (~1,900 SMS or ~166 hours of video)

## Troubleshooting

### "Twilio credentials not found"
- Check `.env` file has correct values
- Restart Django server after updating `.env`
- Verify no extra spaces or quotes around values

### "Phone number is not E.164 format"
- All phone numbers must start with `+` and country code
- Example: `+14155551234` (not `4155551234`)

### "Unable to create record: The From phone number is not a valid"
- Your TWILIO_PHONE_NUMBER must be a Twilio number you own
- Check Phone Numbers in Twilio Console

### Video token generation fails
- Verify TWILIO_API_KEY_SID starts with `SK`
- Verify TWILIO_ACCOUNT_SID starts with `AC`
- Check API key hasn't been deleted in Twilio Console

## Additional Resources

- Twilio Console: https://console.twilio.com/
- SMS API Docs: https://www.twilio.com/docs/sms
- Video API Docs: https://www.twilio.com/docs/video
- Django Twilio: https://github.com/rdegges/django-twilio
