from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date

from .models import Customer, Loan
from .serializers import (
    RegisterSerializer,
    CheckEligibilitySerializer,
    CreateLoanSerializer,
)
from .utils import (
    calculate_credit_score,
    calculate_monthly_installment,
    check_loan_approval,
)


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Calculate approved limit = 36 * monthly_salary rounded to nearest lakh
        monthly_income = data['monthly_income']
        approved_limit = round((36 * monthly_income) / 100000) * 100000

        customer = Customer(
            first_name=data['first_name'],
            last_name=data['last_name'],
            age=data['age'],
            phone_number=data['phone_number'],
            monthly_salary=monthly_income,
            approved_limit=approved_limit,
            current_debt=0,
        )
        customer.save()

        return Response({
            'customer_id': customer.customer_id,
            'name': f"{customer.first_name} {customer.last_name}",
            'age': customer.age,
            'monthly_income': customer.monthly_salary,
            'approved_limit': customer.approved_limit,
            'phone_number': customer.phone_number,
        }, status=status.HTTP_201_CREATED)


class CheckEligibilityView(APIView):
    def post(self, request):
        serializer = CheckEligibilitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            customer = Customer.objects.get(customer_id=data['customer_id'])
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        credit_score = calculate_credit_score(customer)
        approved, corrected_interest_rate = check_loan_approval(
            credit_score,
            data['interest_rate'],
            customer
        )

        monthly_installment = calculate_monthly_installment(
            data['loan_amount'],
            corrected_interest_rate,
            data['tenure']
        )

        return Response({
            'customer_id': customer.customer_id,
            'approval': approved,
            'interest_rate': data['interest_rate'],
            'corrected_interest_rate': corrected_interest_rate,
            'tenure': data['tenure'],
            'monthly_installment': monthly_installment,
        }, status=status.HTTP_200_OK)


class CreateLoanView(APIView):
    def post(self, request):
        serializer = CreateLoanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            customer = Customer.objects.get(customer_id=data['customer_id'])
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        credit_score = calculate_credit_score(customer)
        approved, corrected_interest_rate = check_loan_approval(
            credit_score,
            data['interest_rate'],
            customer
        )

        monthly_installment = calculate_monthly_installment(
            data['loan_amount'],
            corrected_interest_rate,
            data['tenure']
        )

        if not approved:
            return Response({
                'loan_id': None,
                'customer_id': customer.customer_id,
                'loan_approved': False,
                'message': 'Loan not approved based on credit score or EMI limit',
                'monthly_installment': monthly_installment,
            }, status=status.HTTP_200_OK)

        # Create the loan
        loan = Loan.objects.create(
            customer=customer,
            loan_amount=data['loan_amount'],
            tenure=data['tenure'],
            interest_rate=corrected_interest_rate,
            monthly_repayment=monthly_installment,
            emis_paid_on_time=0,
            start_date=date.today(),
            end_date=None,
        )

        return Response({
            'loan_id': loan.loan_id,
            'customer_id': customer.customer_id,
            'loan_approved': True,
            'message': 'Loan approved successfully',
            'monthly_installment': monthly_installment,
        }, status=status.HTTP_201_CREATED)


class ViewLoanView(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.select_related('customer').get(loan_id=loan_id)
        except Loan.DoesNotExist:
            return Response(
                {'error': 'Loan not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        customer = loan.customer

        return Response({
            'loan_id': loan.loan_id,
            'customer': {
                'id': customer.customer_id,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'phone_number': customer.phone_number,
                'age': customer.age,
            },
            'loan_amount': loan.loan_amount,
            'interest_rate': loan.interest_rate,
            'monthly_installment': loan.monthly_repayment,
            'tenure': loan.tenure,
        }, status=status.HTTP_200_OK)


class ViewLoansByCustomerView(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        loans = Loan.objects.filter(customer=customer)

        loan_list = []
        for loan in loans:
            # Calculate repayments left
            if loan.end_date:
                today = date.today()
                if loan.end_date > today:
                    months_left = (loan.end_date.year - today.year) * 12 + \
                                  (loan.end_date.month - today.month)
                else:
                    months_left = 0
            else:
                months_left = loan.tenure - loan.emis_paid_on_time

            loan_list.append({
                'loan_id': loan.loan_id,
                'loan_amount': loan.loan_amount,
                'interest_rate': loan.interest_rate,
                'monthly_installment': loan.monthly_repayment,
                'repayments_left': max(months_left, 0),
            })

        return Response(loan_list, status=status.HTTP_200_OK)