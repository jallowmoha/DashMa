import pandas as pd
import concurrent.futures
from app.utils.database import get_customer_spending, get_all_customers, get_all_transactions, get_customers_in_range
from app.utils.cache import redis_client


first_threshold = 10000
first_multiplier = 0.25
second_threshold = 5000
second_multiplier = 0.2
third_threshold = 2000
third_multiplier = 0.15

def preprocess_transactions_data(transactions_data):
    df = pd.DataFrame(transactions_data, columns=['transaction_id', 'customer_id', 'transaction_date', 'transaction_amount', 'category'])
    df = df[df['category'] == 'prepaid_credit']
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df = df[df['transaction_date'] > (pd.Timestamp.now() - pd.DateOffset(years=1))]
    return df

def calculate_loan_amount(customer_spending):
    if customer_spending >= first_threshold:
        return customer_spending * first_multiplier
    elif customer_spending >= second_multiplier:
        return customer_spending * second_threshold
    elif customer_spending >= third_threshold:
        return customer_spending * third_multiplier
    else:
        return 0
    
"""

def calculate_loan_amount(spending, spending_thresholds, loan_amount_multipliers):
    loan_amount = 0

    for idx, threshold in enumerate(spending_thresholds):
        if spending >= threshold:
            loan_amount = spending * loan_amount_multipliers[idx]
        else:
            break

    return loan_amount """
def calculate_loan_eligibility_for_customer(customer_id, test_spending=None, test_customer_data=None):
    
    #cache_key = f"loan_eligibility:{customer_id}"
    #cached_result = redis_client.get(cache_key)

    """if cached_result:
        return int(cached_result)"""

    if test_spending and test_customer_data:
        spending, customer_data = test_spending, test_customer_data
    else:
        spending, customer_data = get_customer_spending(customer_id)

    print(f"Spending: {spending}, Customer Data: {customer_data}")  
    loan_amount = calculate_loan_amount(spending)
    print(f"Loan Amount: {loan_amount}")  
    if customer_data and loan_amount:
        customer_data['loan_amount'] = loan_amount

    # Cache the result for 1 hour (3600 seconds)
    #redis_client.set(cache_key, loan_amount, ex=3600)

    return loan_amount, customer_data





def process_loan_eligibility_results(loan_eligibility_results):
    eligible_customers = {}
    MIN_LOAN_AMOUNT = 10
    for customer, loan_amount in loan_eligibility_results.items():
        if loan_amount >= MIN_LOAN_AMOUNT:
            eligible_customers[customer] = loan_amount
    return eligible_customers


def calculate_loan_eligibility_for_all_customers(page_size=100000):
    page = 1
    customer_loan = []

    while True:
        customer_ids = get_customers_in_range(page, page_size)
        if not customer_ids: 
            break

        for customer_id in customer_ids:
            try:
                loan, data = calculate_loan_eligibility_for_customer(customer_id)
                if data:
                    customer_loan.append(data)
                    phone_number = data['phone_number']
                    print(f"messaging customer with phone number {phone_number}")
             
            except Exception as e:
                print(f"Error calculating loan eligibility for customer {customer_id}: {e}")

        page += 1

    return customer_loan



#loans = calculate_loan_eligibility_for_all_customers()
#print(loans)