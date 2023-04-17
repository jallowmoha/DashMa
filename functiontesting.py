from sqlalchemy import create_engine, func, inspect
from sqlalchemy.orm import sessionmaker
from app.models import Customer, Transaction, User, CustomerLoanInfo
from app.config import Config
from contextlib import contextmanager
from sqlalchemy.orm import declarative_base, joinedload
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.orm import Session
from typing import Optional


import hashlib




from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship,scoped_session
from app.enummodels import UserRole
import pandas as pd
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.utils.database import get_customer_spending, get_all_customers, get_all_transactions, get_customer_by_id, get_customer_loan_info_by_id
from app.utils.cache import redis_client
from sqlalchemy.engine.url import make_url
#from app.services.loan_calculator import calculate_loan_eligibility_for_all_customers
Base = declarative_base()
engine = create_engine(Config.DATABASE_URI, pool_size=10, max_overflow=20).connect()
Session = sessionmaker(bind=engine)
db = engine

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class Customer(Base):
    __tablename__ = 'customers'

    customer_id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    email = Column(String, unique=True)
    transactions = relationship("Transaction", back_populates="customer")
    loans = relationship("Loan", back_populates="customer")
    def to_dict(self, session: Optional[Session] = None, include_loans=False):
        if session:
            session.add(self)
        result = {
            "id": self.customer_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_number": self.phone_number
        }
        if include_loans:
            if session:
                session.flush()  # Flush the session to synchronize the state
            result["loans"] = [loan.__dict__ for loan in self.loans]
        return result

class Transaction(Base):
    __tablename__ = 'transactions'

    transaction_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    transaction_date = Column(DateTime)
    transaction_amount = Column(Float)
    category = Column(String) 

    customer = relationship("Customer", back_populates="transactions")

class Loan(Base):
    __tablename__ = 'loans'

    loan_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    loan_amount = Column(Float, nullable=False)
    outstanding_balance = Column(Float, nullable=False)
    loan_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)

    customer = relationship("Customer", back_populates="loans")

@contextmanager
def db_session():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def get_customer_spending(session, customer_id):
    session = Session()
    try:
        result = (
            session.query(
                func.sum(Transaction.transaction_amount).label("total_spending"),
                Customer.customer_id,
                Customer.first_name,
                Customer.last_name,
                Customer.phone_number,
            )
            .join(Customer)
            .filter(
                Customer.customer_id == customer_id,
                Transaction.category == "prepaid_credit",
                Transaction.transaction_amount >= 300,
            )
            .group_by(Customer.customer_id)
            .one_or_none()
        )

        if result:
            spending = result.total_spending or 0
            customer_data = {
                "customer_id": result.customer_id,
                "first_name": result.first_name,
                "last_name": result.last_name,
                "phone_number": result.phone_number,
                
            }
            return spending, customer_data
        else:
            return 0, None
    except Exception as e:
        print(f"Error getting customer spending for customer {customer_id}: {e}")
        session.rollback()
        raise
    finally:
        session.close()

#spending, data = get_customer_spending(6)


def get_all_customers():
    with db_session() as session:
        customers = session.query(Customer.customer_id).all()
    return [customer.customer_id for customer in customers]

def get_all_transactions():
    with db_session() as session:
        transactions = (
            session.query(Transaction)
            .filter(Transaction.category == "prepaid_credit")
            .all()
        )
    return [transaction.__dict__ for transaction in transactions]







"""def preprocess_transactions_data(transactions_data):
    df = pd.DataFrame(transactions_data, columns=['transaction_id', 'customer_id', 'transaction_date', 'transaction_amount', 'category'])
    df = df[df['category'] == 'prepaid_credit']
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df = df[df['transaction_date'] > (pd.Timestamp.now() - pd.DateOffset(years=1))]
    return df"""

def calculate_loan_amount(customer_spending):
    if customer_spending >= 1000:
        return customer_spending * 0.25
    elif customer_spending >= 500:
        return customer_spending * 0.2
    elif customer_spending >= 200:
        return customer_spending * 0.15
    else:
        return 0
    

def calculate_loan_eligibility_for_customer(session, customer_id):
    
    #cache_key = f"loan_eligibility:{customer_id}"
    #cached_result = redis_client.get(cache_key)
    

    """if cached_result:
        return int(cached_result)"""

    spending, customer_data = get_customer_spending(session, customer_id)
    loan_amount = calculate_loan_amount(spending)
    if customer_data and loan_amount:
        customer_data['loan_amount'] = loan_amount

    # Cache the result for 1 hour (3600 seconds)
    #redis_client.set(cache_key, loan_amount, ex=3600)

    return loan_amount, customer_data






from concurrent.futures import ThreadPoolExecutor, as_completed


def get_customers_in_range(page, page_size):
    start = (page - 1) * page_size
    end = start + page_size
    with db_session() as session:
        customers = session.query(Customer.customer_id).slice(start, end).all()
    return [customer.customer_id for customer in customers]


import concurrent.futures

def calculate_loan_eligibility_for_customer_wrapper(customer_id):
    session = Session()  # Create a new session for this thread
    try:
        result = calculate_loan_eligibility_for_customer(session, customer_id)
        session.commit()  # Commit the transaction if successful
    except Exception as e:
        print(f"Error calculating loan eligibility for customer {customer_id}: {e}")
        session.rollback()  # Rollback the transaction in case of an error
    finally:
        session.close()  # Close the session when done
    return result




def calculate_loan_eligibility_for_all_customers(page_size=100000):
    page = 1
    customer_loan = []

    while True:
        customer_ids = get_customers_in_range(page, page_size)
        if not customer_ids:
            break

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = [result for result in executor.map(calculate_loan_eligibility_for_customer_wrapper, customer_ids)]


        for result in results:
            if result is not None:
                customer_loan.append(result)

        page += 1

    return customer_loan


#customer = calculate_loan_eligibility_for_customer_wrapper(6)
#print(customer)

"""
customer_loan = get_customer_loan_info_by_id(5)


print(customer_loan)
print(db)
database_url = Config.DATABASE_URI
parsed_url = make_url(database_url)
database_name = parsed_url.database

print(f"Database name: {database_name}")"""
"""def get_all_customers():
    session = Session()
    all_customers = session.query(CustomerLoanInfo).all()
    session.close()
    return all_customers

# Example usage
loan_info = get_all_customers()
for info in loan_info:
    print(info.loan_id, info.loan_amount, info.interest_rate, info.term_weeks, info.start_date, info.end_date, info.balance)"""



all_customers = calculate_loan_eligibility_for_all_customers(10000)
print(all_customers)