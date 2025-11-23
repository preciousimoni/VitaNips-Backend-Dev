from django.db.models import Avg, Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import VitalSign, ExerciseLog, SleepLog, HealthInsight, HealthGoal

class HealthAnalyticsService:
    @staticmethod
    def generate_weekly_summary(user, end_date=None):
        end_date = end_date or timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        # Aggregate data
        # For VitalSign, we need to aggregate by type which means checking non-null columns
        # This is a bit complex with the flattened model. 
        # We'll do a simplified aggregation for key metrics.
        
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
            # Calculate duration in hours for each log and average it
            # Since duration is a property, we can't use aggregate directly on it easily in basic Django ORM without annotation
            # We'll do it in python for simplicity or use raw SQL/ExpressionWrapper
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
            # 'goals_progress': self.calculate_goals_progress(user) # TODO: Implement this
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

