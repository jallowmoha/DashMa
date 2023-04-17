# app/__init__.py
from flask import Flask
from flask_jwt_extended import JWTManager
from app.config import Config
from app.utils.database import Base, engine
from app.routes import routes
from app.auth import auth
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import os
from sqlalchemy import  create_engine

flask_env = os.environ.get('FLASK_ENV', 'development')
env_path = os.path.join(os.path.dirname(__file__), f'../.env.{flask_env}')
load_dotenv(dotenv_path=env_path, override=True)


engine = create_engine(Config.DATABASE_URI, pool_size=10, max_overflow=0).connect()
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    CORS(app)
    app.config.from_object(config_class)
    app.db = SQLAlchemy(app)
    migrate = Migrate(app, app.db)

    # Initialize JWT
    jwt = JWTManager(app)

    # Create the database tables
    Base.metadata.create_all(engine)

    # Register the blueprints
    app.register_blueprint(routes, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app


