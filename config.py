import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///parking.db'  # Use MySQL in production
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)
