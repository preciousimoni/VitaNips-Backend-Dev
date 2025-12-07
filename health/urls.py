from django.urls import path
from .views import (
    VitalSignListCreateView, VitalSignDetailView, VitalSignLatestView, PatientVitalSignsView,
    FoodLogListCreateView, FoodLogDetailView,
    ExerciseLogListCreateView, ExerciseLogDetailView,
    SleepLogListCreateView, SleepLogDetailView,
    HealthGoalListCreateView, HealthGoalDetailView,
    MedicalDocumentListCreateView, MedicalDocumentDetailView,
    WaterIntakeLogListCreateView, WaterIntakeTodayView,
    HealthInsightListView, WeeklySummaryView
)
from .sharing_views import (
    DocumentShareCreateView, SharedWithMeListView, 
    DocumentShareListView, DocumentShareDeleteView
)
from .analytics_views import HealthRecommendationsView, HealthTrendView

urlpatterns = [
    path('vital-signs/', VitalSignListCreateView.as_view(), name='vital-sign-list'),
    path('vital-signs/latest/', VitalSignLatestView.as_view(), name='vital-sign-latest'),
    path('vital-signs/<int:pk>/', VitalSignDetailView.as_view(), name='vital-sign-detail'),
    path('patients/<int:user_id>/vital-signs/', PatientVitalSignsView.as_view(), name='patient-vital-signs'),
    
    path('food-logs/', FoodLogListCreateView.as_view(), name='food-log-list'),
    path('food-logs/<int:pk>/', FoodLogDetailView.as_view(), name='food-log-detail'),
    
    path('exercise-logs/', ExerciseLogListCreateView.as_view(), name='exercise-log-list'),
    path('exercise-logs/<int:pk>/', ExerciseLogDetailView.as_view(), name='exercise-log-detail'),
    
    path('sleep-logs/', SleepLogListCreateView.as_view(), name='sleep-log-list'),
    path('sleep-logs/<int:pk>/', SleepLogDetailView.as_view(), name='sleep-log-detail'),
    
    path('health-goals/', HealthGoalListCreateView.as_view(), name='health-goal-list'),
    path('health-goals/<int:pk>/', HealthGoalDetailView.as_view(), name='health-goal-detail'),
    
    path('water-logs/', WaterIntakeLogListCreateView.as_view(), name='water-log-list'),
    path('water/today/', WaterIntakeTodayView.as_view(), name='water-today'),
    
    path('insights/', HealthInsightListView.as_view(), name='health-insight-list'),
    path('summary/weekly/', WeeklySummaryView.as_view(), name='weekly-summary'),
    
    # Analytics
    path('recommendations/', HealthRecommendationsView.as_view(), name='health-recommendations'),
    path('trends/<str:metric_type>/', HealthTrendView.as_view(), name='health-trends'),
    
    # Documents
    path('documents/', MedicalDocumentListCreateView.as_view(), name='medical-document-list'),
    path('documents/<int:pk>/', MedicalDocumentDetailView.as_view(), name='medical-document-detail'),
    path('documents/share/', DocumentShareCreateView.as_view(), name='document-share-create'),
    path('documents/shared-with-me/', SharedWithMeListView.as_view(), name='shared-with-me-list'),
    path('documents/<int:pk>/shared-with/', DocumentShareListView.as_view(), name='document-shared-with-list'),
    path('documents/shares/<int:pk>/', DocumentShareDeleteView.as_view(), name='document-share-delete'),
]
