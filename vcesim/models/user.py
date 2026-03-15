from datetime import datetime, UTC
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from vcesim.ui import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    first_name = db.Column(db.String(200))
    last_name = db.Column(db.String(200))
    course = db.Column(db.String(150))
    instructor = db.Column(db.String(100))
    role = db.Column(db.String(20), default="student")
    must_change_password = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))

    def __init__(self, username=None, password_hash=None, email=None, 
                 first_name=None, last_name=None, course=None, 
                 instructor=None, role=None, must_change_password=None):
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.course = course
        self.instructor = instructor
        self.role = role
        self.must_change_password = must_change_password

    def __repr__(self):
        return f"User {self.username}"
    
    def __str__(self):
        return self.__class__.__name__ + ": " + self.username
    
    def get_id(self):
        return self.id

@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))