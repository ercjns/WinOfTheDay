from datetime import datetime
from os import urandom
from binascii import b2a_base64
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from . import db
from . import bcrypt



class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(60), unique=True)
    _password = db.Column(db.String(128))
    salt = db.Column(db.String(32))
    email = db.Column(db.String(120))
    name = db.Column(db.String(50))
    isMod = db.Column(db.Boolean)

    def __init__(self, username, password, email=None, name=None, isMod=False):
        self.username = username
        self.password = password
        self.email = email
        self.name = name
        self.isMod = isMod

    def __repr__(self):
        return '<User {0}>'.format(self.username)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self.salt = b2a_base64(urandom(32))
        self._password = bcrypt.generate_password_hash(self.salt+plaintext)

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self._password, self.salt+plaintext)

    def getName(self):
        if self.name is not None:
            return self.name
        return self.username



class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(350))
    user_id = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    isApproved = db.Column(db.Boolean)
    mod_time = db.Column(db.DateTime)

    def __init__(self, content=None, user_id=None, isApproved=None, mod_time=None):
        self.content = content
        self.user_id = user_id
        self.create_time = datetime.now()
        self.isApproved = isApproved
        self.mod_time = mod_time

    def __repr__(self):
        return '<Post {0}>'.format(self.id)