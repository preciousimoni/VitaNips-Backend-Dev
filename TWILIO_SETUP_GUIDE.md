# Twilio Setup Guide for VitaNips SOS Feature

## Current Issue
Your `.env` file has:
```
TWILIO_PHONE_NUMBER=+2348149960190
```

This appears to be your personal phone number, NOT a Twilio phone number. Twilio requires you to send SMS from a Twilio-owned phone number.

## Error Encountered
```
Twilio Error 21266: 'To' and 'From' number cannot be the same
```

This happens when your emergency contact's number is the same as your Twilio sender number.

## Solution: Get a Twilio Phone Number

### Option 1: Trial Account (Free - For Testing)

1. **Log in to Twilio Console**
   - Go to: https://console.twilio.com/
   
2. **Get a Trial Phone Number**
   - When you sign up, Twilio gives you a free trial number
   - Go to: **Phone Numbers** → **Manage** → **Active Numbers**
   - You should see your trial number there
   
3. **Update Your .env File**
   ```bash
   TWILIO_PHONE_NUMBER=+15551234567  # Replace with your Twilio trial number
   ```

4. **Limitations of Trial Account**
   - ⚠️ Can only send SMS to **verified phone numbers**
   - ⚠️ SMS includes "Sent from your Twilio trial account" prefix
   - ✅ Perfect for development and testing
   
5. **Verify Emergency Contact Numbers**
   - Go to: **Phone Numbers** → **Manage** → **Verified Caller IDs**
   - Click **Add a new number**
   - Enter your emergency contact's number
   - Complete the verification process

### Option 2: Upgrade Account (Paid - For Production)

1. **Upgrade Your Account**
   - Go to: https://console.twilio.com/billing
   - Click **Upgrade**
   - Add payment method
   
2. **Buy a Phone Number**
   - Go to: **Phone Numbers** → **Buy a Number**
   - Select your country (Nigeria: +234)
   - Choose a number with SMS capability
   - Purchase the number (~$1-2/month)
   
3. **Update Your .env File**
   ```bash
   TWILIO_PHONE_NUMBER=+234XXXXXXXXXX  # Your purchased Twilio number
   ```

4. **Benefits**
   - ✅ Send SMS to any number (no verification needed)
   - ✅ No trial message prefix
   - ✅ Production-ready

### Option 3: Development Mode (No SMS)

If you just want to test the SOS feature without actual SMS:

1. **Comment out Twilio credentials in .env**
   ```bash
   # TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   # TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   # TWILIO_PHONE_NUMBER=+1234567890
   ```

2. **The system will:**
   - ✅ Create emergency alerts in database
   - ✅ Log all SOS events
   - ✅ Return success response
   - ⚠️ Skip actual SMS sending
   - 📝 Add note: "SMS not sent: Twilio service not configured"

## Current Configuration Check

Your current Twilio credentials:
```
TWILIO_ACCOUNT_SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER: +2348149960190 ❌ (This should be a Twilio number)
```

## Steps to Fix Right Now

### Quick Fix (Recommended for Testing):

1. **Find your Twilio trial number:**
   ```bash
   # Log in to: https://console.twilio.com/
   # Navigate to: Phone Numbers > Manage > Active Numbers
   # Copy your trial number (should look like: +1 XXX XXX XXXX)
   ```

2. **Update .env file:**
   ```bash
   TWILIO_PHONE_NUMBER=+1XXXXXXXXXX  # Your Twilio trial number
   ```

3. **Verify your emergency contact numbers:**
   - Add your emergency contact numbers as verified caller IDs
   - This allows them to receive SMS during trial

4. **Restart Django server:**
   ```bash
   # Press Ctrl+C in the terminal running the server
   python manage.py runserver
   ```

5. **Test SOS again**

## Testing After Fix

### 1. Add Emergency Contact
```bash
POST http://localhost:8000/api/emergency/contacts/
{
  "name": "Test Contact",
  "relationship": "Friend",
  "phone_number": "+1234567890",  # Use a verified number for trial
  "email": "test@example.com"
}
```

### 2. Trigger SOS
```bash
POST http://localhost:8000/api/emergency/trigger_sos/
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "message": "Testing SOS after Twilio fix"
}
```

### 3. Check Logs
You should see:
```
✓ SMS sent to Test Contact (+1234567890), SID: SM..., Status: queued
```

Instead of:
```
✗ Error sending SMS to Test Contact: 'To' and 'From' number cannot be the same
```

## Alternative: Use SMS Gateway Service

If Twilio doesn't work well for Nigeria, consider:

1. **Africa's Talking** (Better for African numbers)
   - https://africastalking.com/
   - Better rates for Nigeria
   - Easier setup for +234 numbers

2. **Termii** (Nigeria-specific)
   - https://www.termii.com/
   - Nigeria-focused SMS service
   - Better delivery rates in Nigeria

3. **Infobip**
   - https://www.infobip.com/
   - Global SMS service
   - Good coverage in Africa

## Need Help?

If you're still having issues:
1. Share your Twilio trial number
2. Confirm you've verified your emergency contact numbers
3. Check the server logs for specific errors

## Summary

✅ **What's Working:**
- SOS feature is functional
- Emergency alerts are being created
- Location is being captured
- System handles Twilio errors gracefully

❌ **What Needs Fixing:**
- Update `TWILIO_PHONE_NUMBER` to use an actual Twilio phone number
- Verify emergency contact numbers if using trial account

🎯 **Next Steps:**
1. Get your Twilio trial number from console
2. Update `.env` file
3. Verify emergency contact numbers
4. Restart server and test

---

**Current Status:** SOS feature is working but SMS not sending due to phone number configuration issue. Once fixed, SMS will be sent successfully! 📱
