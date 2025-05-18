class Config():
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATION = True

class LocalDevelopmentConfig(Config):
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///vpav2.sqlite3'
    DEBUG = True

    SECRET_KEY = 'secret-key'
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = 'password-salt'
    WTF_CSRF_ENABLED = False
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'