# Add to pharmacy/views.py

class VerifyBankAccountView(views.APIView):
    """
    Verify bank account details in real-time.
    POST /api/pharmacy/portal/verify-account/
    """
    permission_classes = [permissions.IsAuthenticated, IsPharmacyStaffOfOrderPharmacy]

    def post(self, request, *args, **kwargs):
        account_number = request.data.get('account_number')
        account_bank = request.data.get('account_bank')
        
        if not account_number or not account_bank:
            return Response(
                {'error': 'Account number and bank code are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify account with Flutterwave
        from payments.utils import verify_bank_account
        
        result = verify_bank_account(account_number, account_bank)
        
        if result:
            return Response(result)
        else:
            return Response(
                {'status': 'error', 'message': 'Failed to verify account'},
                status=status.HTTP_400_BAD_REQUEST
            )
