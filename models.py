#!/usr/bin/env python3
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text)
    oauth_token = db.Column(db.Text)
    oauth_token_secret = db.Column(db.Text)

    def __repr__(self):
        return f'<User @{self.name} {self.id}>'
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return str(self.id)

if __name__ == '__main__':
    import os
    from flask import Flask
    test_app = Flask('test_app')
    test_app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URI']
    test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(test_app)
    from IPython import embed
    with test_app.app_context():
        embed()
