from flask import Flask, request, redirect, session, make_response
from flask.cli import AppGroup
from mako.lookup import TemplateLookup
import haml
import os
from flask_login import LoginManager, login_user, logout_user, \
    login_required, current_user
from authlib.integrations.requests_client import OAuth1Session
import uuid
from datetime import datetime
from contextlib import contextmanager
from models import db, User, Invite, Upload
from flask_migrate import Migrate
import capnp
import rpc_capnp

FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
URI = 'http://localhost:5000' if FLASK_ENV == 'development' else 'https://neettv.rje.li'
DB_URI = 'postgres://postgres:postgres@localhost/neettv'

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET']
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = '/'
login_manager.init_app(app)

templates = TemplateLookup(['templates'], preprocessor=haml.preprocessor)
def render_template(path, **kwargs):
    return templates.get_template(path).render(current_user=current_user, **kwargs)

@app.cli.command('repl')
def cli_repl():
    from IPython import embed; embed()

# ?
def get_mss():
    mss_conn = capnp.TwoPartyClient('localhost:60000')
    mss = mss_conn.bootstrap().cast_as(rpc_capnp.MpvSockServer)
    return mss

TWITTER_ID = os.environ.get('TWITTER_ID')
TWITTER_SECRET = os.environ.get('TWITTER_SECRET')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def root():
    if current_user.is_authenticated:
        userscript_path = '/static/neettv.user.js?nocache='+str(uuid.uuid4())
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
    twitter_id = access_token['user_id']
    user = User.query.filter_by(twitter_id=twitter_id).first()
    if user is None:
        print('twitter id not found, creating new user')
        code = session.pop('invite_code', None)
        if code is None:
            return redirect('/')
        user = User(
            name=access_token['screen_name'],
            twitter_id=twitter_id,
            twitter_token=access_token['oauth_token'],
            twitter_secret=access_token['oauth_token_secret'],
            invite=code)
        db.session.add(user)
    else:
        print('twitter id found')
        user.twitter_token = access_token['oauth_token']
        user.twitter_secret = access_token['oauth_token_secret']
    db.session.commit()
    login_user(user)
    return redirect('/')

@app.route('/invite')
def invite():
    if current_user.is_authenticated:
        inv = Invite(code=str(uuid.uuid4())[:8], creator=current_user.id)
        db.session.add(inv)
        db.session.commit()
        return render_template('invite.haml', link=URI+'/invite?c='+inv.code)
    else:
        code = request.args.get('c')
        session['invite_code'] = code
        return redirect('/twitterlogin')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/search')
@login_required
def search():
    return render_template('search.haml')

@app.route('/watch', methods=['POST'])
@login_required
def watch():
    print(request.json)
    path = 'ytdl://youtube.com/watch?v='+request.json['videoId']
    print(type(path))
    print(get_mss().execute(str(current_user.id), { 'loadFile': { 'path': path } }).wait())
    return ''

@app.route('/api/upload', methods=['POST'])
@login_required
def upload():
    print('upload!', request, request.files)
    for k, v in request.form.items():
        print('form:', k, v)
    payload = request.files['payload'].read()
    print('payload size:', len(payload))
    upload = Upload(
        location=request.form['location'],
        type=request.form['type'],
        created_at=datetime.utcnow(),
        uploader=current_user.id,
        payload=payload)
    db.session.add(upload)
    db.session.commit()
    # print(request.files['formk'])
    # print(len(request.data))
    # data = request.get_data()
    # print('size:', len(data), type(data))
    return ''

if __name__ == '__main__':
    app.run()
