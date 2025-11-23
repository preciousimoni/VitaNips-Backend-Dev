from celery import shared_task
from django.contrib.auth import get_user_model
from .services import HealthAnalyticsService
from .models import HealthInsight

User = get_user_model()

@shared_task
def generate_daily_insights():
    users = User.objects.all() # In production, filter by is_active=True
    for user in users:
        try:
            insights = HealthAnalyticsService.detect_anomalies(user)
            if insights:
                HealthInsight.objects.bulk_create(insights)
        except Exception as e:
            print(f"Error generating insights for user {user.id}: {e}")

@shared_task
def send_weekly_health_report():
    # Placeholder for sending reports
    # users = User.objects.filter(profile__weekly_report_enabled=True)
    # for user in users:
    #     summary = HealthAnalyticsService.generate_weekly_summary(user)
    #     send_email(...)
    pass

