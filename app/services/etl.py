import requests
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import pymysql
from app.config import Config
# Replace with your API URL and authentication details
API_URL = "https://api.example.com/customers"
API_AUTH = {"api_key": "your_api_key"}

# Replace with your Cloud SQL credentials
DB_USERNAME = "your_username"
DB_PASSWORD = "your_password"
DB_HOST = "your_cloud_sql_host"
DB_PORT = "your_cloud_sql_port"
DB_NAME = "your_database_name"

def extract_data(api_url, api_auth):
    headers = {"Authorization": f"Bearer {api_auth['api_key']}"}
    params = {"limit": 100000}  # Retrieve 100,000 records
    response = requests.get(api_url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        raise Exception(f"API request failed with status code {response.status_code}")

def transform_data(data):
    df = pd.DataFrame(data)

    # Add your data transformation logic here
    # Example: Convert date string to datetime object
    # df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

    return df

def load_data(df, db_username, db_password, db_host, db_port, db_name):
    connection_string = f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(connection_string)

    # Replace 'your_table_name' with your actual table name
    df.to_sql('your_table_name', engine, if_exists='replace', index=False)

def run_etl():
    data = extract_data(API_URL, API_AUTH)
    transformed_data = transform_data(data)
    load_data(transformed_data, DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

if __name__ == "__main__":
    run_etl()
