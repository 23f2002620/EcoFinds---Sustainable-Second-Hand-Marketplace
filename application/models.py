from .database import db
from flask_security import UserMixin, RoleMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(100), unique = True, nullable = False)
    password = db.Column(db.String(200), nullable = False)
    fs_uniquifier = db.Column(db.String(100), unique = True, nullable = False)
    active = db.Column(db.Boolean, nullable = False)
    name = db.Column(db.String(100), nullable = False)
    address = db.Column(db.String(200), nullable = False)
    pincode = db.Column(db.Integer, nullable = False)
    Reserveparkingspot = db.relationship('Reserveparkingspot', backref = 'bearer')
    roles = db.relationship('Role', backref = 'bearer', secondary = 'user_roles')

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(10), unique = True, nullable = False)
    description = db.Column(db.String(100))

class UserRoles(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

class Parkinglot(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    prime_location_name = db.Column(db.String(100), nullable = False)
    price = db.Column(db.Integer, nullable = False)
    address = db.Column(db.String(200), nullable = False)
    pincode = db.Column(db.Integer, nullable = False)
    number_of_spots = db.Column(db.Integer, nullable = False)
    parkingspots = db.relationship('Parkingspot', backref = 'Parkinglot')

class Parkingspot(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parkinglot.id'))
    status = db.Column(db.String(1), nullable = False)
    spotid = db.relationship('Reserveparkingspot', backref = 'Parkingspot')

class Reserveparkingspot(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parkingspot.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    parking_timestamp = db.Column(db.DateTime, nullable = False)
    leaving_timestamp = db.Column(db.DateTime, nullable = False)
    parking_cost = db.Column(db.Integer, nullable = False)