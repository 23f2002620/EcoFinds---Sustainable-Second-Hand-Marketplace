from flask import Flask
from application.database import db
from application.models import User, Role
from application.config import LocalDevelopmentConfig
from flask_security import Security, SQLAlchemyUserDatastore
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__)
    app.config.from_object(LocalDevelopmentConfig)
    db.init_app(app)
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    app.security = Security(app, datastore)
    app.app_context().push()
    return app

app = create_app()

with app.app_context():
    db.create_all()

    app.security.datastore.find_or_create_role(name = 'admin', description = 'Superuser')
    app.security.datastore.find_or_create_role(name = 'user', description = 'GeneralUser')
    db.session.commit()

    if not app.security.datastore.find_user(email = "user@admin.com"):
        app.security.datastore.create_user(email = "user@admin.com",
                                           password = generate_password_hash("admin123"),
                                           name = "admin",
                                           address = "admin",
                                           pincode = 000000,
                                           roles = ['admin'])    

    if not app.security.datastore.find_user(email = "user1@user.com"):
        app.security.datastore.create_user(email = "user1@user.com",
                                           password = generate_password_hash("user123"),
                                           name = "user1",
                                           address = "user1",
                                           pincode = 000000,
                                           roles = ['user'])
    db.session.commit()

if __name__ == '__main__':
    app.run()     

