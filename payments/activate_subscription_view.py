

class ActivatePharmacySubscriptionView(APIView):
    """
    Manually activate the latest pharmacy subscription (for debugging/admin use)
    POST /api/payments/subscriptions/pharmacy/activate/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Check if user is pharmacy staff
        if not request.user.is_pharmacy_staff or not hasattr(request.user, 'works_at_pharmacy'):
            return Response(
                {'error': 'User is not associated with a pharmacy'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pharmacy = request.user.works_at_pharmacy
        
        # Get the latest subscription record for this pharmacy
        subscription = PharmacySubscriptionRecord.objects.filter(
            pharmacy=pharmacy
        ).order_by('-created_at').first()
        
        if not subscription:
            return Response(
                {'error': 'No subscription found for this pharmacy'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Activate the subscription
        subscription.status = 'active'
        subscription.save()
        
        # Update pharmacy expiry
        pharmacy.subscription_expiry = subscription.current_period_end
        pharmacy.save()
        
        return Response({
            'message': 'Subscription activated successfully',
            'pharmacy': pharmacy.name,
            'expiry_date': pharmacy.subscription_expiry,
            'subscription_id': subscription.id
        })
