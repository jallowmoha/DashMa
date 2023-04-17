from flask import jsonify, Blueprint, render_template,  request
#from app import app
from app.services.loan_calculator import calculate_loan_amount, calculate_loan_eligibility_for_all_customers, preprocess_transactions_data
from app.services.messaging import notify_customer
from app.utils.database import get_customer_spending, db_session
from app.config import Config
from flask_jwt_extended import jwt_required
from app.models import Loan, Customer, CustomerInformation, CustomerLoanInfo, CustomerCreditScore
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime as dt

engine = create_engine(Config.DATABASE_URI).connect()
Session = sessionmaker(bind=engine)

routes = Blueprint('routes', __name__)

@routes.route("/loan-eligibility/<customer_id>", methods=["GET"])
@jwt_required()
def loan_eligibility(customer_id):
    customer_id = int(customer_id)
    customer_spending, customer_data = get_customer_spending(customer_id)
    print("Fetched customer data:", customer_data)

    if not customer_data:
        return jsonify({"msg": "Customer not found"}), 404

    loan_amount = calculate_loan_amount(customer_spending)

    with db_session() as session:
        #customer_data["customer_id"] = customer_data.pop("id")
        customer_data_instance = Customer(**customer_data)

        #session.add(customer_data_instance)

        #session.commit()

        response_data = {
            "customer_id": customer_id,
            "first_name": customer_data['first_name'],
            "last_name": customer_data['last_name'],
            "phone_number": customer_data['phone_number'],
           
            "loan_amount": loan_amount
        }

        if loan_amount > 0:
            print("Loan amount is " + str(loan_amount))
            # Send text message
            #notify_customer(customer_data.get("phone_number"), customer_data.get("first_name"), loan_amount)

    return jsonify(response_data)




@routes.route("/eligible_customers", methods=["GET"])
@jwt_required()
def get_eligible_customers():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 1000))

    eligible_customers = calculate_loan_eligibility_for_all_customers(page_size)

    start = (page - 1) * page_size
    end = start + page_size

    paginated_customers = eligible_customers[start:end]

    return jsonify(paginated_customers)

@routes.route('/api/loans', methods=['GET'])
@jwt_required()
def get_loans():
    with db_session() as session:
        loans = session.query(
            Customer.first_name,
            Customer.last_name,
            Loan.loan_amount,
            Loan.outstanding_balance,
            Loan.loan_date,
            Loan.due_date
        ).join(
            Loan, Loan.customer_id == Customer.customer_id
        ).all()

    loans_data = [
        {
            "first_name": loan.first_name,
            "last_name": loan.last_name,
            "loan_amount": loan.loan_amount,
            "outstanding_balance": loan.outstanding_balance,
            "loan_date": loan.loan_date,
            "due_date": loan.due_date
        }
        for loan in loans
    ]

    return jsonify(loans_data)


@routes.route('/api/customers/<int:customer_id>/loans', methods=['GET'])
@jwt_required()
def get_customer_loans(customer_id):
    with db_session() as session:
        customer_loans = session.query(
            Customer.first_name,
            Customer.last_name,
            Loan.loan_amount,
            Loan.outstanding_balance,
            Loan.loan_date,
            Loan.due_date
        ).join(
            Loan, Loan.customer_id == Customer.customer_id
        ).filter(
            Customer.customer_id == customer_id
        ).all()

    if not customer_loans:
        return jsonify({"message": "Customer not found or has no loans"}), 404

    loans_data = [
        {
            "first_name": loan.first_name,
            "last_name": loan.last_name,
            "loan_amount": loan.loan_amount,
            "outstanding_balance": loan.outstanding_balance,
            "loan_date": loan.loan_date,
            "due_date": loan.due_date
        }
        for loan in customer_loans
    ]

    return jsonify(loans_data)



@routes.route('/landing')
@jwt_required()
def landing():
    return render_template('landing.html')

#------------------------------------------------- CUSTOMER LOAN INFORMATION ROUTES----------------------------

@routes.route('/api/add_customer', methods=['POST'])
#@jwt_required()
def add_customer():
    data = request.get_json()
    print(data)
    customer = CustomerInformation(
        first_name=data['first_name'],
        last_name=data['last_name'],
        DOB=data['DOB'],
        tin_number=data['tin_number'],
        #id_number=data['id_number'],
        phone_number=data['phone_number'],
        address=data['address'],
    )
    session = Session()
    session.add(customer)
    session.flush() 
  
   
    loan = CustomerLoanInfo (
        loan_amount = data['loan_amount'],
        start_date = data['start_date'],
        interest_rate = 20,
        term_weeks = 12,
        end_date=CustomerLoanInfo.calculate_end_date(data['start_date'], 12),
        balance=CustomerLoanInfo.initial_balance(int(data['loan_amount']), 20),
        customer_id = customer.customer_id
   

    )


    session.add(loan)
    session.commit()

    return jsonify({"message": "Customer added successfully"}), 201

@routes.route('/api/search_customer_loan', methods=['GET'])
#@jwt_required()
def search_customer_loan():
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    tin_number = request.args.get('tin_number')
    dob = request.args.get('DOB')

    print(f"first_name: {first_name}, last_name: {last_name},tin_number: {tin_number}, dob: {dob}")


    if dob:
        dob = dt.strptime(dob, "%Y-%m-%d").date()

    session = Session()

    query = session.query(CustomerLoanInfo).join(CustomerInformation)

    if first_name:
        query = query.filter(CustomerInformation.first_name == first_name)
    if last_name:
        query = query.filter(CustomerInformation.last_name == last_name)
    if tin_number:
        query = query.filter(CustomerInformation.tin_number == tin_number)
    if dob:
        query = query.filter(CustomerInformation.DOB == dob)

    loans = query.all()
    print("Customer Loan", loans)

    if loans:
        return jsonify([loan.serialize() for loan in loans]), 200
    else:
        return jsonify({"message": "No loans found"}), 404


@routes.route('/api/get_customer_credit_score', methods=['GET'])
@jwt_required()
def get_customer_credit_score():
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    tin_number = request.args.get('tin_number')
    dob = request.args.get('DOB')

    session = Session()
    credit_score = (
        session.query(CustomerCreditScore)
        .join(CustomerInformation)
        .filter(
            CustomerInformation.first_name == first_name,
            CustomerInformation.last_name == last_name,
            CustomerInformation.tin_number == tin_number,
            CustomerInformation.DOB == dob,
        )
        .first()
    )

    if credit_score:
        return jsonify(credit_score.serialize()), 200
    else:
        return jsonify({"message": "Credit score not found"}), 404