# vitanips/core/push_notifications.py
"""
Helper module for sending push notifications using FCM v1 API
Supports both the new service account method and legacy API key
"""

import logging
from typing import Dict, List, Optional
from django.conf import settings
from push_notifications.models import GCMDevice as FCMDevice

logger = logging.getLogger(__name__)

# Check if we have firebase-admin for FCM v1 API
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FCM_V1_AVAILABLE = True
except ImportError:
    FCM_V1_AVAILABLE = False
    logger.warning("firebase-admin not installed. Install with: pip install firebase-admin")


def initialize_firebase():
    """Initialize Firebase Admin SDK if service account is available"""
    if not FCM_V1_AVAILABLE:
        return False
    
    service_account_path = settings.PUSH_NOTIFICATIONS_SETTINGS.get('FCM_SERVICE_ACCOUNT_KEY')
    
    if not service_account_path:
        logger.debug("No FCM service account key configured")
        return False
    
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            logger.info("✓ Firebase Admin SDK initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        return False


def send_fcm_notification(
    user,
    title: str,
    body: str,
    data: Optional[Dict] = None,
    image_url: Optional[str] = None
) -> Dict[str, int]:
    """
    Send push notification to all user's FCM devices
    
    Args:
        user: User object
        title: Notification title
        body: Notification body
        data: Additional data payload (optional)
        image_url: Image URL for rich notification (optional)
    
    Returns:
        Dictionary with success and failure counts
    """
    results = {'success': 0, 'failure': 0}
    
    # Get all active FCM devices for the user
    devices = FCMDevice.objects.filter(user=user, active=True)
    
    if not devices.exists():
        logger.debug(f"No active FCM devices for user {user.id}")
        return results
    
    # Try FCM v1 API first (modern method)
    if initialize_firebase():
        results = _send_via_fcm_v1(devices, title, body, data, image_url)
    else:
        # Fall back to legacy API
        logger.debug("Using legacy FCM API")
        results = _send_via_legacy_api(devices, title, body, data)
    
    logger.info(
        f"Push notification sent to user {user.id}: "
        f"{results['success']} succeeded, {results['failure']} failed"
    )
    
    return results


def _send_via_fcm_v1(
    devices,
    title: str,
    body: str,
    data: Optional[Dict] = None,
    image_url: Optional[str] = None
) -> Dict[str, int]:
    """Send notifications using FCM HTTP v1 API"""
    results = {'success': 0, 'failure': 0}
    
    for device in devices:
        try:
            # Build the message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image_url if image_url else None
                ),
                data=data if data else {},
                token=device.registration_id,
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=title,
                        body=body,
                        icon='/logo.png',
                        badge='/badge.png'
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link=data.get('url') if data else None
                    )
                )
            )
            
            # Send the message
            response = messaging.send(message)
            logger.debug(f"Successfully sent message to device {device.id}: {response}")
            results['success'] += 1
            
        except messaging.UnregisteredError:
            logger.warning(f"Device {device.id} is unregistered, marking as inactive")
            device.active = False
            device.save()
            results['failure'] += 1
            
        except Exception as e:
            logger.error(f"Failed to send to device {device.id}: {e}")
            results['failure'] += 1
    
    return results


def _send_via_legacy_api(
    devices,
    title: str,
    body: str,
    data: Optional[Dict] = None
) -> Dict[str, int]:
    """Send notifications using legacy FCM API (via django-push-notifications)"""
    results = {'success': 0, 'failure': 0}
    
    try:
        # Use django-push-notifications' send_message method
        response = devices.send_message(
            title=title,
            body=body,
            data=data if data else {}
        )
        
        # Count successes and failures
        if hasattr(response, 'success'):
            results['success'] = response.success
            results['failure'] = response.failure
        else:
            # Fallback if response format is different
            results['success'] = devices.count()
            
    except Exception as e:
        logger.error(f"Failed to send via legacy API: {e}")
        results['failure'] = devices.count()
    
    return results


def send_notification_to_user(
    user,
    notification_type: str,
    title: str,
    body: str,
    url: Optional[str] = None,
    extra_data: Optional[Dict] = None
) -> bool:
    """
    Convenience function to send a notification to a user
    
    Args:
        user: User object
        notification_type: Type of notification (e.g., 'appointment_reminder')
        title: Notification title
        body: Notification body
        url: URL to navigate to when notification is clicked
        extra_data: Additional data to include
    
    Returns:
        True if at least one notification was sent successfully
    """
    data = {
        'type': notification_type,
        'timestamp': str(timezone.now())
    }
    
    if url:
        data['url'] = url
    
    if extra_data:
        data.update(extra_data)
    
    results = send_fcm_notification(user, title, body, data)
    return results['success'] > 0


# Import timezone at the end to avoid circular imports
from django.utils import timezone
