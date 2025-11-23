from rest_framework import views, permissions
from rest_framework.response import Response
from .services import HealthRecommendationEngine

class HealthRecommendationsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        recommendations = HealthRecommendationEngine.generate_recommendations(request.user)
        return Response(recommendations)

class HealthTrendView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, metric_type):
        days = int(request.query_params.get('days', 30))
        trend_data = HealthRecommendationEngine.predict_health_trends(
            request.user,
            metric_type,
            days
        )
        return Response(trend_data)

