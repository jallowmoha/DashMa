import pytest
from app import create_app
from app.models import User, Customer, CustomerInformation, CustomerLoanInfo, CustomerCreditScore, Loan, Transaction
from app.utils.database import add_user, get_user_by_email, get_customer_by_id, get_transaction_by_id
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from app.config import Config
from werkzeug.security import generate_password_hash
from app.config import TestingConfig



Base = declarative_base()
engine = create_engine(TestingConfig.SQLALCHEMY_DATABASE_URI).connect()
Session = sessionmaker()



@pytest.fixture(scope="module")
def test_client():
    # Create a test client using the TestingConfig
    app = create_app()
    app.config.from_object(TestingConfig)
    
    # Set up the in-memory SQLite database
    Base.metadata.create_all(bind=engine)
    Session.configure(bind=engine)
    app.db = Session
    
    with app.test_client() as test_client:
        yield test_client, Base, engine

    Base.metadata.drop_all(bind=engine)



@pytest.fixture
def db_session(test_client):
    _, Base, engine = test_client
    Session = sessionmaker(bind=engine)

    session = Session()
    yield session
    session.rollback()
    session.close()

def test_signup(test_client, db_session):
    test_client, Base, engine = test_client

    response = test_client.post('/signup', data={'email': 'test@example.com', 'password': 'testpassword'})
    assert response.status_code == 302
    with test_client.application.app_context():
        user = get_user_by_email('test@example.com')
        assert user is not None

def test_login(test_client, db_session):
    test_client, Base, engine = test_client

    email = 'test@example.com'
    password_hash = 'testpassword'

    existing_user = get_user_by_email(email)
    if existing_user is None:
        add_user(email, password_hash)

    response = test_client.post('/login', json={'email': email, 'password': 'testpassword'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'access_token' in json_data




def test_loan_eligibility(test_client):
    test_client, Base, engine = test_client

    # Add required data to test database
    with test_client.application.app_context():

        # Add a customer
        id = 1
        existing_customer = get_customer_by_id(id)
        print("Existing customer: ", existing_customer)
        if existing_customer is None:
            customer = Customer(customer_id=1, first_name='John', last_name='Doe', phone_number='1234567890')
            test_client.application.db.session.add(customer)
            test_client.application.db.session.commit()
            print("Customer created:", customer)
            print("Customer ID:", customer.customer_id)

        else:
            print("Customer already exists:", existing_customer)

        existing_transaction = get_transaction_by_id(id)
        if existing_transaction is None:
            transaction = Transaction(customer_id=1, transaction_amount=5000, category="prepaid_credit")
            test_client.application.db.session.add(transaction)
            test_client.application.db.session.commit()
            print("Transaction created:", transaction)
            print("Customer ID:", transaction.customer_id)

    # Get JWT token
    response = test_client.post('/login', json={'email': 'test@example.com', 'password': 'testpassword'})
    print("this is the response", response.get_json())
    access_token = response.get_json()['access_token']

    response = test_client.get('/loan-eligibility/1', headers={'Authorization': f'Bearer {access_token}'})
    if response.status_code != 200:
        print("Unexpected response:", response.data)
    assert response.status_code == 200
    json_data = response.get_json() 
    assert json_data['customer_id'] == 1
    assert json_data['loan_amount'] >= 0


"""def test_get_eligible_customers(test_client, app):
    # Add required data to test database
    with app.app_context():

        # Add a customer
        id = 1
        existing_customer = get_customer_by_id(id)
        if existing_customer is None:
            customer = Customer(customer_id=1, first_name='John', last_name='Doe', phone_number='1234567890')
            app.db.session.add(customer)
            app.db.session.commit()

    # Get JWT token
    response = test_client.post('/login', json={'email': 'test@example.com', 'password': 'testpassword'})
    access_token = response.get_json()['access_token']

    response = test_client.get('/eligible_customers', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data) > 0"""

def test_get_loans(test_client, db_session):
    test_client, Base, engine = test_client

    # Add required data to test database
    with test_client.application.app_context():

        # Add a customer
        customer = Customer(
            first_name='John',
            last_name='Doe',
            email='johndoe@example.com',
            phone_number='1234567890',
        )
        db_session.add(customer)
        db_session.commit()

        # Add a loan
        loan = Loan(
            customer_id=customer.customer_id,
            loan_amount=1000,
            outstanding_balance=800,
            loan_date='2023-01-01',
            due_date='2023-12-31',
        )
        db_session.add(loan)
        db_session.commit()

    response = test_client.post('/login', json={'email': 'test@example.com', 'password': 'testpassword'})
    print("this is the response", response.get_json())
    access_token = response.get_json()['access_token']

    # Perform a GET request to the endpoint
    response = test_client.get('/api/loans', headers={'Authorization': f'Bearer {access_token}'})

    # Check the response status code
    assert response.status_code == 200

    # Check the response data
    json_data = response.get_json()
    print(json_data)
    assert json_data[0]['first_name'] == 'John'
    assert json_data[0]['last_name'] == 'Doe'
    assert json_data[0]['loan_amount'] == 1000
    assert json_data[0]['outstanding_balance'] == 800
    """assert json_data[0]['loan_date'] == '2023-01-01'
    assert json_data[0]['due_date'] == '2023-12-31'"""

