from datetime import date


def calculate_credit_score(customer):
    loans = customer.loans.all()

    if not loans.exists():
        return 50  # default score for new customers

    # Component 1: Past loans paid on time
    total_emis = sum(loan.tenure for loan in loans)
    emis_on_time = sum(loan.emis_paid_on_time for loan in loans)
    if total_emis > 0:
        on_time_ratio = emis_on_time / total_emis
    else:
        on_time_ratio = 0

    # Component 2: Number of loans taken in past
    num_loans = loans.count()
    if num_loans <= 2:
        loan_count_score = 20
    elif num_loans <= 5:
        loan_count_score = 15
    else:
        loan_count_score = 10

    # Component 3: Loan activity in current year
    current_year = date.today().year
    current_year_loans = loans.filter(start_date__year=current_year).count()
    if current_year_loans == 0:
        activity_score = 20
    elif current_year_loans <= 2:
        activity_score = 15
    else:
        activity_score = 10

    # Component 4: Loan approved volume
    total_loan_volume = sum(loan.loan_amount for loan in loans)
    if total_loan_volume < customer.approved_limit * 0.5:
        volume_score = 20
    elif total_loan_volume < customer.approved_limit:
        volume_score = 15
    else:
        volume_score = 10

    # Component 5: Check if current debt exceeds approved limit
    current_debt = sum(
        loan.loan_amount for loan in loans
        if loan.end_date is None or loan.end_date >= date.today()
    )
    if current_debt > customer.approved_limit:
        return 0

    # Calculate final score out of 100
    on_time_score = on_time_ratio * 40  # 40 points for on time payments
    final_score = on_time_score + loan_count_score + activity_score + volume_score

    return min(round(final_score), 100)


def calculate_monthly_installment(loan_amount, interest_rate, tenure):
    # Compound interest EMI formula
    monthly_rate = interest_rate / (12 * 100)

    if monthly_rate == 0:
        return round(loan_amount / tenure, 2)

    emi = loan_amount * monthly_rate * (1 + monthly_rate) ** tenure / \
          ((1 + monthly_rate) ** tenure - 1)

    return round(emi, 2)


def check_loan_approval(credit_score, interest_rate, customer):
    approved = False
    corrected_interest_rate = interest_rate

    # Check if sum of current EMIs > 50% of monthly salary
    current_loans = customer.loans.filter(end_date__gte=date.today())
    total_emis = sum(loan.monthly_repayment for loan in current_loans)

    if total_emis > 0.5 * customer.monthly_salary:
        return False, corrected_interest_rate

    # Approve based on credit score
    if credit_score > 50:
        approved = True
        corrected_interest_rate = interest_rate

    elif 30 < credit_score <= 50:
        if interest_rate > 12:
            approved = True
            corrected_interest_rate = interest_rate
        else:
            approved = True
            corrected_interest_rate = 12

    elif 10 < credit_score <= 30:
        if interest_rate > 16:
            approved = True
            corrected_interest_rate = interest_rate
        else:
            approved = True
            corrected_interest_rate = 16

    else:
        approved = False

    return approved, corrected_interest_rate