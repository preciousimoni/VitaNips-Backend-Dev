# VitaNips Backend

The backend API for the VitaNips health management platform, built with Django and Django Rest Framework. This robust API powers the frontend application, handling data management, authentication, real-time communications, and background tasks.

## 🚀 Features

*   **RESTful API**: Comprehensive API endpoints for all platform features.
*   **Authentication**: Secure user authentication using JWT and Firebase integration.
*   **Real-time Updates**: WebSocket support via Django Channels for real-time notifications and chat.
*   **Background Tasks**: Asynchronous task processing with Celery and Redis (e.g., sending emails, processing health data).
*   **Geo-location**: Geospatial queries for finding doctors and pharmacies using PostGIS.
*   **Push Notifications**: Integration with Firebase Cloud Messaging (FCM).
*   **Payment Processing**: Secure payment handling.
*   **API Documentation**: Auto-generated Swagger/OpenAPI documentation.