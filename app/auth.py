
from flask import request, jsonify, Blueprint, render_template, redirect, url_for, flash
from app.utils.database import db_session, add_user, get_user_by_email, engine
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app.models import User, UserRole
from sqlalchemy.orm import sessionmaker


Session = sessionmaker(bind=engine)
db_session_maker = Session()

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash("Email and password are required")
            return redirect(url_for('auth.signup'))

        with db_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if user:
                flash("User with this email already exists")
                return redirect(url_for('auth.signup'))

        hashed_password = generate_password_hash(password)
        add_user(email, hashed_password)

        flash("User created")
        return redirect(url_for('auth.login'))
    return render_template('signup.html')


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    print(f"Email: {email}")
    print(f"Password: {password}")

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    user = db_session_maker.query(User).filter(User.email == email).first()
    print(f"User: {user}")

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid email or password'}), 401

    # Create the access token
    access_token = create_access_token(identity=user.user_id)

    # If the user is an admin, show the landing page with buttons
    if user.role == UserRole.ADMIN:
        print("logged in as admin...")
        return jsonify({'access_token': access_token}), 200
    else:
        # If the user is not an admin, return the access token
        print("logged in as user...")
        return jsonify({'access_token': access_token}), 200

