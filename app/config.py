import os
from dotenv import load_dotenv


flask_env = os.environ.get('FLASK_ENV', 'production')
flask_env = 'production'
env_path = os.path.join(os.path.dirname(__file__), f'../.env.{flask_env}')
load_dotenv(dotenv_path=env_path, override=True)
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URI = os.environ.get("DATABASE_URL")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///testing.db'  # Using a separate SQLite database for testing
    SQLALCHEMY_DATABASE_URI = os.environ.get("TESTING_DB_URL")



print("flask env: ", flask_env)
print("Database: ", Config.SQLALCHEMY_DATABASE_URI)
#print(os.environ)
print("Environment: ", env_path)