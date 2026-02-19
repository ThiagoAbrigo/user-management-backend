from os import environ, path
from dotenv import load_dotenv

config_dir = path.abspath(path.dirname(__file__)) 
base_dir = path.abspath(path.join(config_dir, '..', '..')) 
load_dotenv(path.join(base_dir, '.env'))

class Config:
    #genaral configuration
    FLASK_APP = environ.get('FLASK_APP')
    FLASK_ENV = environ.get('FLASK_ENV')
    
    # PostgreSQL config
    user = environ.get("PGUSER")
    password = environ.get("PGPASSWORD")
    host = environ.get("PGHOST")
    db = environ.get("PGDATABASE")
    port = environ.get("PGPORT", "5432")
    print(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    JWT_SECRET_KEY = environ.get("JWT_SECRET_KEY")

    # [NUEVO] URL del API externo (Docker del profesor)
    PERSON_API_URL = "http://localhost:8096/api/person"

    #SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = f'postgresql://{user}:{password}@{host}:{port}/{db}?client_encoding=utf8'
    
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_RECORS_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = 'enable'