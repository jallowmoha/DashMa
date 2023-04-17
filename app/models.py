from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey, Date, DECIMAL, create_engine
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base
from app.enummodels import UserRole
from typing import Optional
from sqlalchemy.orm import sessionmaker
from app.config import Config
from datetime import timedelta, datetime

from sqlalchemy import event


engine = create_engine(Config.DATABASE_URI, pool_size=10, max_overflow=0).connect()
Session = sessionmaker(bind=engine)
Base = declarative_base()
Session = sessionmaker(bind=engine)

#----------------------------------------- Loan Eligibility database--------------------------------

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




#-------------------------------------LOANS Database------------------------------------------------------------------------




class CustomerInformation(Base):
    __tablename__ = 'customer_information'
    customer_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    DOB = Column(Date, nullable=False)
    tin_number = Column(String(20))
    id_number = Column(String(20))
    phone_number = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)

    loans = relationship("CustomerLoanInfo", back_populates="customer")
    credit_score = relationship("CustomerCreditScore", back_populates="customer", uselist=False)

    def serialize(self):
        return {
            "customer_id": self.customer_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "DOB": self.DOB.isoformat(),
            "tin_number": self.tin_number,
            "id_number": self.id_number,
            "phone_number": self.phone_number,
            "address": self.address,
            "loans": [loan.serialize() for loan in self.loans],
            "credit_score": self.credit_score.serialize() if self.credit_score else None,
        }

class CustomerLoanInfo(Base):
    __tablename__ = 'customer_loan_info'
    loan_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customer_information.customer_id'))
    loan_amount = Column(DECIMAL(10, 2), nullable=False)
    interest_rate = Column(DECIMAL(5, 2), nullable=False)
    term_weeks = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    balance = Column(DECIMAL(10, 2))

    customer = relationship("CustomerInformation", back_populates="loans")
    repayments = relationship("RepaymentInfo", back_populates="loan")

    def serialize(self):
        return {
            "loan_id": self.loan_id,
            "customer_id": self.customer_id,
            "loan_amount": str(self.loan_amount),
            "interest_rate": str(self.interest_rate),
            "term_weeks": self.term_weeks,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "balance": str(self.balance),
        }
    def initial_balance(loan_amount, interest_rate):
        if not loan_amount or not interest_rate:
            return None
        balance = loan_amount + (interest_rate/100) * loan_amount
        return balance
  
    def calculate_end_date(start_date, term_weeks):
        if not start_date or not term_weeks:
            return None
        start_date = datetime.strptime(str(start_date), '%Y-%m-%d')  # parse start_date as a datetime object
        delta = timedelta(weeks=term_weeks)
        return start_date + delta

class CustomerCreditScore(Base):
    __tablename__ = 'customer_credit_score'
    customer_id = Column(Integer, ForeignKey('customer_information.customer_id'), primary_key=True)
    credit_score = Column(Integer, nullable=False)

    customer = relationship("CustomerInformation", back_populates="credit_score")
    def serialize(self):
        return {
            "customer_id": self.customer_id,
            "credit_score": self.credit_score,
        }

class RepaymentInfo(Base):
    __tablename__ = 'repayment_info'
    repayment_id = Column(Integer, primary_key=True)
    loan_id = Column(Integer, ForeignKey('customer_loan_info.loan_id'))
    repayment_amount = Column(DECIMAL(10, 2), nullable=False)
    repayment_date = Column(Date, nullable=False)

    loan = relationship("CustomerLoanInfo", back_populates="repayments")
    def serialize(self):
        return {
            "repayment_id": self.repayment_id,
            "loan_id": self.loan_id,
            "repayment_amount": str(self.repayment_amount),
            "repayment_date": self.repayment_date.isoformat(),
        }

# Replace "mysql_username", "mysql_password", and "localhost" with your MySQL credentials and host.


# Drop all tables if they exist (optional, for testing purposes)
#Base.metadata.drop_all(engine)

# Create tables
#Base.metadata.create_all(engine)



@event.listens_for(RepaymentInfo, 'after_insert')
def update_loan_balance(mapper, connection, target):
    loan_id = target.loan_id
    loan = connection.execute(
        "SELECT loan_amount FROM customer_loan_info WHERE loan_id = :loan_id",
        loan_id=loan_id,
    ).fetchone()

    repayments = connection.execute(
        "SELECT SUM(repayment_amount) as total_repayment FROM repayment_info WHERE loan_id = :loan_id",
        loan_id=loan_id,
    ).fetchone()

    new_balance = loan['loan_amount'] - (repayments['total_repayment'] or 0)

    connection.execute(
        "UPDATE customer_loan_info SET balance = :balance WHERE loan_id = :loan_id",
        balance=new_balance,
        loan_id=loan_id,
    )




