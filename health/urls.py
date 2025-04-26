from django.urls import path
from .views import (
    VitalSignListCreateView, VitalSignDetailView,
    SymptomLogListCreateView, SymptomLogDetailView,
    FoodLogListCreateView, FoodLogDetailView,
    ExerciseLogListCreateView, ExerciseLogDetailView,
    SleepLogListCreateView, SleepLogDetailView,
    HealthGoalListCreateView, HealthGoalDetailView,
    MedicalDocumentListCreateView, MedicalDocumentDetailView,
)

urlpatterns = [
    path('vital-signs/', VitalSignListCreateView.as_view(), name='vital-sign-list'),
    path('vital-signs/<int:pk>/', VitalSignDetailView.as_view(), name='vital-sign-detail'),
    path('symptoms/', SymptomLogListCreateView.as_view(), name='symptom-log-list'),
    path('symptoms/<int:pk>/', SymptomLogDetailView.as_view(), name='symptom-log-detail'),
    path('food-logs/', FoodLogListCreateView.as_view(), name='food-log-list'),
    path('food-logs/<int:pk>/', FoodLogDetailView.as_view(), name='food-log-detail'),
    path('exercise-logs/', ExerciseLogListCreateView.as_view(), name='exercise-log-list'),
    path('exercise-logs/<int:pk>/', ExerciseLogDetailView.as_view(), name='exercise-log-detail'),
    path('sleep-logs/', SleepLogListCreateView.as_view(), name='sleep-log-list'),
    path('sleep-logs/<int:pk>/', SleepLogDetailView.as_view(), name='sleep-log-detail'),
    path('health-goals/', HealthGoalListCreateView.as_view(), name='health-goal-list'),
    path('health-goals/<int:pk>/', HealthGoalDetailView.as_view(), name='health-goal-detail'),
    path('documents/', MedicalDocumentListCreateView.as_view(), name='medical-document-list'),
    path('documents/<int:pk>/', MedicalDocumentDetailView.as_view(), name='medical-document-detail'),
]