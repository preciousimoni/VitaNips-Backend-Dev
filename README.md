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

## 🛠️ Tech Stack

*   **Framework**: [Django](https://www.djangoproject.com/)
*   **API Framework**: [Django Rest Framework (DRF)](https://www.django-rest-framework.org/)
*   **Database**: [PostgreSQL](https://www.postgresql.org/) with PostGIS
*   **Async Tasks**: [Celery](https://docs.celeryq.dev/)
*   **Message Broker**: [Redis](https://redis.io/)
*   **WebSockets**: [Django Channels](https://channels.readthedocs.io/)
*   **Authentication**: [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/) + [Firebase Admin](https://firebase.google.com/docs/admin/setup)
*   **Documentation**: [drf-spectacular](https://drf-spectacular.readthedocs.io/) (OpenAPI 3.0)
*   **Storage**: Django Storages (AWS S3 compatible)

## 📦 Installation & Getting Started

Follow these steps to set up the backend locally:

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd VitaNips-Backend-Dev
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Setup:**
    Copy `.env.example` to `.env` and configure your environment variables:
    ```bash
    cp .env.example .env
    ```
    *Ensure you set up your database credentials, Redis URL, and Firebase credentials.*

5.  **Apply database migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser:**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```
    The API will be available at `http://localhost:8000/`.

## 📚 API Documentation

Once the server is running, you can access the interactive API documentation at:

*   **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
*   **Redoc**: `http://localhost:8000/api/schema/redoc/`

## 🧪 Testing

Run the test suite to ensure everything is working correctly:

```bash
pytest
```

## 📄 License

This project is licensed under the MIT License.
