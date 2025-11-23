from django.db.models import Avg, Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import VitalSign, ExerciseLog, SleepLog, HealthInsight, HealthGoal, WaterIntakeLog

class HealthAnalyticsService:
    @staticmethod
    def generate_weekly_summary(user, end_date=None):
        end_date = end_date or timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        vital_stats = {}
        vitals = VitalSign.objects.filter(
            user=user,
            date_recorded__date__range=[start_date, end_date]
        )
        
        if vitals.exists():
            vital_stats['heart_rate_avg'] = vitals.aggregate(Avg('heart_rate'))['heart_rate__avg']
            vital_stats['systolic_bp_avg'] = vitals.aggregate(Avg('systolic_pressure'))['systolic_pressure__avg']
            vital_stats['diastolic_bp_avg'] = vitals.aggregate(Avg('diastolic_pressure'))['diastolic_pressure__avg']
            vital_stats['weight_avg'] = vitals.aggregate(Avg('weight'))['weight__avg']
        
        exercise_stats = ExerciseLog.objects.filter(
            user=user,
            datetime__date__range=[start_date, end_date]
        ).aggregate(
            total_duration=Sum('duration'),
            total_calories=Sum('calories_burned'),
            workout_count=Count('id')
        )
        
        sleep_stats = {}
        sleep_logs = SleepLog.objects.filter(
            user=user,
            sleep_time__date__range=[start_date, end_date]
        )
        if sleep_logs.exists():
            total_duration = sum([log.duration for log in sleep_logs])
            avg_duration = total_duration / sleep_logs.count()
            avg_quality = sleep_logs.aggregate(Avg('quality'))['quality__avg']
            sleep_stats = {
                'avg_duration': avg_duration,
                'avg_quality': avg_quality
            }
        
        return {
            'period': f'{start_date} to {end_date}',
            'vitals': vital_stats,
            'exercise': exercise_stats,
            'sleep': sleep_stats,
        }
    
    @staticmethod
    def detect_anomalies(user):
        insights = []
        
        # Blood Pressure Trend
        recent_bp = VitalSign.objects.filter(
            user=user,
            systolic_pressure__isnull=False,
            date_recorded__gte=timezone.now() - timedelta(days=7)
        ).order_by('-date_recorded')[:5]
        
        if recent_bp.count() >= 3:
            high_readings = sum(1 for bp in recent_bp 
                              if bp.systolic_pressure > 140)
            if high_readings >= 2:
                insights.append(HealthInsight(
                    user=user,
                    insight_type='warning',
                    title='Elevated Blood Pressure Detected',
                    description='Multiple high readings in the past week. Consider consulting your doctor.',
                    related_metric='blood_pressure',
                    priority='high'
                ))
        
        # Exercise streak
        exercise_days = ExerciseLog.objects.filter(
            user=user,
            datetime__date__gte=timezone.now().date() - timedelta(days=7)
        ).dates('datetime', 'day').distinct().count()
        
        if exercise_days >= 5:
            insights.append(HealthInsight(
                user=user,
                insight_type='achievement',
                title='Great Exercise Streak!',
                description=f'You exercised {exercise_days} days this week!',
                related_metric='exercise',
                priority='low'
            ))
            
        return insights

class HealthRecommendationEngine:
    @staticmethod
    def generate_recommendations(user):
        recommendations = []
        
        # Analyze recent health data
        recent_exercise = ExerciseLog.objects.filter(
            user=user,
            datetime__date__gte=timezone.now().date() - timedelta(days=30)
        )
        
        # Exercise recommendations
        exercise_count = recent_exercise.count()
        if exercise_count < 8:  # Less than 2x per week
            recommendations.append({
                'category': 'exercise',
                'priority': 'high',
                'title': 'Increase Physical Activity',
                'description': 'Try to exercise at least 3-4 times per week for optimal health.',
                'action': 'Set exercise goal',
                'action_url': '/health/goals/create?type=exercise'
            })
        
        # Sleep recommendations
        recent_sleep = SleepLog.objects.filter(
            user=user,
            sleep_time__date__gte=timezone.now().date() - timedelta(days=7)
        )
        
        if recent_sleep.exists():
            # Calculate average duration in minutes
            total_minutes = sum([log.duration * 60 for log in recent_sleep])
            avg_sleep_minutes = total_minutes / recent_sleep.count()
            
            if avg_sleep_minutes < 420:  # Less than 7 hours
                recommendations.append({
                    'category': 'sleep',
                    'priority': 'medium',
                    'title': 'Improve Sleep Duration',
                    'description': f'Your average sleep is {avg_sleep_minutes/60:.1f} hours. Aim for 7-9 hours.',
                    'action': 'View sleep tips',
                    'action_url': '/health/insights/sleep-tips'
                })
        
        # Hydration recommendations
        today_water = WaterIntakeLog.objects.filter(
            user=user,
            date=timezone.now().date()
        ).aggregate(Sum('amount_ml'))['amount_ml__sum'] or 0
        
        if today_water < 2000:  # Less than 2L
            recommendations.append({
                'category': 'hydration',
                'priority': 'low',
                'title': 'Stay Hydrated',
                'description': f'You\'ve had {today_water}ml today. Target: 2000ml.',
                'action': 'Log water',
                'action_url': '/health/water'
            })
        
        return recommendations
    
    @staticmethod
    def predict_health_trends(user, metric_type, days=30):
        """Simple trend prediction using linear regression (simplified implementation)"""
        # Note: Scikit-learn is heavy, we'll use a simpler approach or assume it's installed
        # For simplicity in this environment, we'll implement a basic linear regression manually
        # if numpy/sklearn are not available, or use them if they are.
        
        vitals = VitalSign.objects.filter(
            user=user,
            date_recorded__gte=timezone.now() - timedelta(days=days)
        ).order_by('date_recorded')

        data_points = []
        if metric_type == 'blood_pressure':
             vitals = vitals.filter(systolic_pressure__isnull=False)
             for v in vitals:
                 data_points.append((v.date_recorded, v.systolic_pressure)) # Analyzing systolic for simplicity
        elif metric_type == 'weight':
             vitals = vitals.filter(weight__isnull=False)
             for v in vitals:
                 data_points.append((v.date_recorded, v.weight))
        else:
            return None

        if len(data_points) < 3:
            return None
        
        # Simple linear regression logic
        # x = days from start, y = value
        start_time = data_points[0][0]
        x = [(p[0] - start_time).days for p in data_points]
        y = [p[1] for p in data_points]
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi ** 2 for xi in x)
        
        if (n * sum_xx - sum_x ** 2) == 0:
             slope = 0
        else:
             slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)
        
        intercept = (sum_y - slope * sum_x) / n
        
        # Predict next 7 days
        last_day = x[-1]
        predictions = []
        for i in range(1, 8):
            future_day = last_day + i
            pred_value = slope * future_day + intercept
            predictions.append(pred_value)
            
        return {
            'trend': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
            'slope': slope,
            'predictions': predictions,
            'confidence': 0.8 # Mock confidence for custom implementation
        }
