import pytest
from app.services.loan_calculator import (
    preprocess_transactions_data,
    calculate_loan_amount,
    calculate_loan_eligibility_for_customer,
    process_loan_eligibility_results,
    calculate_loan_eligibility_for_all_customers,
)
from unittest.mock import patch
from unittest.mock import MagicMock
from app.utils.cache import redis_client
# Add your tests here
def test_preprocess_transactions_data():
    transactions_data = [
        {
            'transaction_id': 1,
            'customer_id': 1,
            'transaction_date': '2023-01-01',
            'transaction_amount': 100,
            'category': 'prepaid_credit'
        },
        {
            'transaction_id': 2,
            'customer_id': 1,
            'transaction_date': '2021-12-31',
            'transaction_amount': 200,
            'category': 'prepaid_credit'
        },
        {
            'transaction_id': 3,
            'customer_id': 1,
            'transaction_date': '2023-01-01',
            'transaction_amount': 300,
            'category': 'other'
        }
    ]
    
    df = preprocess_transactions_data(transactions_data)
    assert df.shape[0] == 1
    assert df.iloc[0]['transaction_amount'] == 100


@pytest.mark.parametrize("spending, expected_loan_amount", [
    (12000, 3000),
    (7000, 1400),
    (3000, 450),
    (1000, 0),
])
def test_calculate_loan_amount(spending, expected_loan_amount):
    assert calculate_loan_amount(spending) == expected_loan_amount




def test_calculate_loan_eligibility_for_customer():
    customer_id = 1
    spending = 12000
    customer_data = {
        'customer_id': customer_id,
        'first_name': 'John',
        'last_name': 'Doe',
        'phone_number': '5551234567'
    }

    # Remove any cached result before running the test
    cache_key = f"loan_eligibility:{customer_id}"
    redis_client.delete(cache_key)

    loan_amount, data = calculate_loan_eligibility_for_customer(customer_id, spending, customer_data)
    assert loan_amount == 3000
    assert data['loan_amount'] == 3000



def test_process_loan_eligibility_results():
    loan_eligibility_results = {
        1: 3000,
        2: 5,
        3: 1000
    }

    eligible_customers = process_loan_eligibility_results(loan_eligibility_results)
    assert len(eligible_customers) == 2
    assert eligible_customers[1] == 3000
    assert eligible_customers[3] == 1000
