import os

class Config:
    SECRET_KEY = 'educlass-super-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123580@localhost/educlass_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024