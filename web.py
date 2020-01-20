from flask import Flask, request, redirect, session, make_response
from mako.lookup import TemplateLookup
import haml
import os
from flask_login import LoginManager, login_user, logout_user, \
    login_required, current_user
from authlib.integrations.requests_client import OAuth1Session
import uuid
from contextlib import contextmanager
from models import db, User
from flask_migrate import Migrate

FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
URI = 'http://localhost:5000' if FLASK_ENV == 'development' else 'https://neettv.rje.li'

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.login_view = '/'
login_manager.init_app(app)
templates = TemplateLookup(['templates'], preprocessor=haml.preprocessor)
def render_template(path, **kwargs):
    return templates.get_template(path).render(current_user=current_user, **kwargs)

TWITTER_ID = os.environ.get('TWITTER_ID')
TWITTER_SECRET = os.environ.get('TWITTER_SECRET')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def root():
    if current_user.is_authenticated:
        userscript_path = '/static/neettvsidecar.user.js?nocache='+str(uuid.uuid4())
        return render_template('home.haml', userscript_path=userscript_path)
    else:
        return render_template('login.haml')

@app.route('/twitterlogin')
def twitterlogin():
    print('performing twitter login')
    client = OAuth1Session(TWITTER_ID, TWITTER_SECRET, redirect_uri=URI+'/twitterauth')
    req_token_url = 'https://api.twitter.com/oauth/request_token'
    req_token = client.fetch_request_token(req_token_url)
    print('req_token:', req_token)
    auth_url = 'https://api.twitter.com/oauth/authenticate'
    session['oauth_token_secret'] = req_token['oauth_token_secret']
    return redirect(client.create_authorization_url(auth_url))

@app.route('/twitterauth')
def twitterauth():
    token = request.args.get('oauth_token')
    token_secret = session.pop('oauth_token_secret', None)
    client = OAuth1Session(TWITTER_ID, TWITTER_SECRET,
        token=token, token_secret=token_secret)
    verifier = request.args.get('oauth_verifier')
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    access_token = client.fetch_access_token(access_token_url, verifier)
    print('access token:', access_token)
    user_id = int(access_token['user_id'])
    # race condition...
    user = User.query.get(user_id)
    if user is None:
        user = User(id=user_id, name=access_token['screen_name'],
            oauth_token=access_token['oauth_token'],
            oauth_token_secret=access_token['oauth_token_secret'])
        db.session.add(user)
    else:
        user.oauth_token = access_token['oauth_token']
        user.oauth_token_secret = access_token['oauth_token_secret']
    db.session.commit()
    login_user(user)
    return redirect('/')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/search')
@login_required
def search():
    return render_template('search.haml')

if __name__ == '__main__':
    app.run()
