from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models import Customer, Transaction, User, CustomerLoanInfo
from app.config import Config
from contextlib import contextmanager
from sqlalchemy.ext.declarative import declarative_base
import hashlib

Base = declarative_base()
engine = create_engine(Config.DATABASE_URI).connect()
Session = sessionmaker(bind=engine)
db = engine
min_transaction = 300

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

def get_customer_spending(customer_id):
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
                Customer.customer_id == Transaction.customer_id,
                Transaction.category == "prepaid_credit",
                Transaction.transaction_amount >= min_transaction,
                Customer.customer_id == customer_id,
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


def get_transaction_by_id(id):
    with db_session() as session:
        transaction = session.query(Transaction).filter(Transaction.customer_id == id).first()
        print("Trasaction in get_transaction_by_id", transaction)
    return transaction

def get_customers_in_range(page, page_size):
    start = (page - 1) * page_size
    end = start + page_size
    with db_session() as session:
        customers = session.query(Customer.customer_id).slice(start, end).all()
    return [customer.customer_id for customer in customers]



def add_user(email, password_hash, role='USER'):
    with db_session() as session:
        user = User(email=email, password_hash=password_hash, role=role)
        session.add(user)
    

def get_user_by_email(email):
    with db_session() as session:
        user = session.query(User).filter(User.email == email).first()
        session.commit()
        session.close()
    return user


def get_customer_by_id(id):
    with db_session() as session:
        customer = session.query(Customer).filter(Customer.customer_id == id).first()
        print("Customer in get_customer_by_id:", customer)
    return customer

def get_customer_by_email(email):
    with db_session() as session:
        customer = session.query(Customer).filter(Customer.email == email).first()
        print("Customer in get_customer_by_id:", customer)
    return customer


def get_customer_loan_info_by_id(id):
    with db_session() as session:
        customer = session.query(CustomerLoanInfo).filter(CustomerLoanInfo.loan_id == id).all()
        session.close()
        print("Customer in get_customer_by_id:", customer)
    return customer