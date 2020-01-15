from flask import Flask, request, redirect
from mako.lookup import TemplateLookup
import haml
import os
from flask_login import LoginManager, login_user, current_user
from authlib.integrations.requests_client import OAuth1Session
from redis import Redis
from psycopg2.pool import ThreadedConnectionPool as PGPool
from contextlib import contextmanager

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET']
login_manager = LoginManager()
login_manager.login_view = '/'
login_manager.init_app(app)
templates = TemplateLookup(['templates'], preprocessor=haml.preprocessor)
def render_template(path, **kwargs):
    return templates.get_template(path).render(current_user=current_user, **kwargs)

TWITTER_ID = os.environ['TWITTER_ID']
TWITTER_SECRET = os.environ['TWITTER_SECRET']
PG_USER = os.environ['PG_USER']
PG_PASS = os.environ['PG_PASS']

redis = Redis()
pg = PGPool(1, 20,
    host='localhost', dbname='neettv',
    user=PG_USER, password=PG_PASS)

@contextmanager
def pg_cursor(commit=False):
    conn = pg.getconn()
    cursor = conn.cursor()
    yield cursor
    if commit:
        conn.commit()
    cursor.close()

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
        with pg_cursor() as cur:
            cur.execute('select name from users where id = %s', (user_id,))
            self.name = cur.fetchone()[0]
    def get_id(self):
        return self.user_id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def root():
    if current_user.is_authenticated:
        return render_template('home.haml')
    else:
        return render_template('login.haml')

@app.route('/twitterlogin')
def twitterlogin():
    print('performing twitter login')
    client = OAuth1Session(TWITTER_ID, TWITTER_SECRET)
    req_token_url = 'https://api.twitter.com/oauth/request_token'
    req_token = client.fetch_request_token(req_token_url)
    print('req_token:', req_token)
    redis.set('oauth:'+req_token['oauth_token'], req_token['oauth_token_secret'])
    auth_url = 'https://api.twitter.com/oauth/authenticate'
    return redirect(client.create_authorization_url(auth_url))

@app.route('/twitterauth')
def twitterauth():
    token = request.args.get('oauth_token')
    token_secret = redis.get('oauth:'+token)
    client = OAuth1Session(TWITTER_ID, TWITTER_SECRET,
        token=token, token_secret=token_secret)
    verifier = request.args.get('oauth_verifier')
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    access_token = client.fetch_access_token(access_token_url, verifier)
    print('access token:', access_token)
    user_id = int(access_token['user_id'])
    with pg_cursor(commit=True) as cur:
        cur.execute('insert into users(id) values(%s) on conflict do nothing;', (user_id,))
        cur.execute('update users set name = %s, oauth_token = %s, oauth_token_secret = %s where id = %s',
            (access_token['screen_name'],
             access_token['oauth_token'], access_token['oauth_token_secret'],
             user_id))
    login_user(User(user_id))
    return redirect('/')
