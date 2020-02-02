#!/usr/bin/env python3
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    twitter_id = db.Column(db.Text)
    twitter_token = db.Column(db.Text)
    twitter_secret = db.Column(db.Text)

    invite = db.Column(db.Text, db.ForeignKey('invites.code'), nullable=False)

    def __repr__(self):
        return f'<User:{self.id} @{self.name}>'
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return str(self.id)

class Invite(db.Model):
    __tablename__ = 'invites'
    code = db.Column(db.Text, primary_key=True)
    creator = db.Column(db.Integer, db.ForeignKey('users.id'))

class Upload(db.Model):
    __tablename__ = 'uploads'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.Text)
    type = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    payload = db.deferred(db.Column(db.LargeBinary))
    uploader = db.Column(db.Integer, db.ForeignKey('users.id'))

class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    src = db.Column(db.Text)
    src_id = db.Column(db.Text)
    title = db.Column(db.Text)